import factory

from qstode.test import FlaskTestCase
from qstode import db
from ..model import User, Bookmark, Tag, Link


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.Session
        exclude = ("_profile",)

    _profile = factory.Faker("profile")

    username = factory.LazyAttribute(lambda obj: obj._profile["username"])
    # if we get a unique username, our email will be unique as well
    email = factory.LazyAttribute(lambda obj: "{.username}@example.com".format(obj))
    display_name = factory.LazyAttribute(lambda obj: obj._profile["name"])
    password = factory.Faker("password")
    active = True
    admin = False


# TODO: it might happen that the same tag gets generated twice. We should find a way to ensure
# that ALL tags are unique.
class TagFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Tag
        sqlalchemy_session = db.Session

    name = factory.Faker("word")


# TODO: this can lead to duplicates
class LinkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Link
        sqlalchemy_session = db.Session

    href = factory.Faker("uri")


class BookmarkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Bookmark
        sqlalchemy_session = db.Session

    title = factory.Faker("sentence", nb_words=6)
    notes = factory.Faker("text")
    private = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        link = LinkFactory()
        # tags = TagFactory.create_batch(3)

        obj = model_class(*args, **kwargs)
        obj.link = link
        # obj.tags = tags
        db.Session.commit()
        return obj

    @factory.post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.user = extracted

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                # qui devo CREARE dei tag object!
                # oppure potrei passare degli oggetti Tag...
                self.tags.append(Tag.get_or_create(tag))


class FactoryModelTest(FlaskTestCase):
    def test_factory_model(self):
        _ = UserFactory()
        db.Session.commit()
        users = User.query.all()
        assert len(users) == 1

    def test_factory_many_models(self):
        _ = UserFactory.create_batch(10)
        db.Session.commit()

        assert User.query.count() == 10

    def test_user_with_bookmarks(self):
        """Create a user, give him some bookmarks, then fetch them."""

        user = UserFactory()
        db.Session.commit()

        _ = BookmarkFactory.create_batch(10, user=user)
        db.Session.commit()

        result = Bookmark.by_user(user.id)
        assert result.count() == 10

    def test_search_by_tags(self):
        """Test for retrieving bookmarks by tags

        1) Create 3 bookmarks
        2) tag 2 bookmarks with "web"
        3) tag 1 bookmark with "search"
        4) count
        """

        user1 = UserFactory(username="pippo")
        user2 = UserFactory(username="gladiolo")
        # I don't need commit() here...
        # db.Session.commit()

        tags1 = ["web", "2.0"]
        tags2 = ["search", "apocalypse"]

        # TODO: qui sarebbe figo poter passare delle tag
        BookmarkFactory.create_batch(2, user=user1, tags=tags1)
        BookmarkFactory.create_batch(1, user=user2, tags=tags2)
        # but I need commit() here, why?
        # because I'm calling Tag.get_or_create() which doesn't save to the database!
        db.Session.commit()

        for tags, count in ((["web"], 2), (["search"], 1)):
            result = Bookmark.by_tags(tags)
            assert result.count() == count

        assert Bookmark.by_user(user1.id).count() == 2
        assert Bookmark.by_user(user2.id).count() == 1
