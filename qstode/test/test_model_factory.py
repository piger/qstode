import factory

from qstode.test import FlaskTestCase
from qstode import db
from ..model import User, Bookmark, Tag, Link


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.Session
        exclude = ('_profile',)

    _profile = factory.Faker('profile')

    username = factory.LazyAttribute(lambda obj: obj._profile["username"])
    email = factory.LazyAttribute(lambda obj: obj._profile["mail"])
    display_name = factory.LazyAttribute(lambda obj: obj._profile["name"])
    password = factory.Faker('password')
    active = True
    admin = False


# TODO: it might happen that the same tag gets generated twice. We should find a way to ensure
# that ALL tags are unique.
class TagFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Tag
        sqlalchemy_session = db.Session

    name = factory.Faker("word")


class LinkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Link
        sqlalchemy_session = db.Session

    href = factory.Faker('uri')


class BookmarkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Bookmark
        sqlalchemy_session = db.Session

    title = factory.Faker('sentence', nb_words=6)
    notes = factory.Faker('text')
    private = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        link = LinkFactory()
        tags = TagFactory.create_batch(3)

        obj = model_class(*args, **kwargs)
        obj.link = link
        obj.tags = tags
        db.Session.commit()
        return obj

    @factory.post_generation
    def user(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.user = extracted


class FactoryModelTest(FlaskTestCase):    
    def test_factory_model(self):
        user = UserFactory()
        db.Session.commit()
        users = User.query.all()
        assert len(users) == 1

    def test_factory_many_models(self):
        users = UserFactory.create_batch(10)
        db.Session.commit()

        assert User.query.count() == 10

    def test_user_with_bookmarks(self):
        """Create a user, give him some bookmarks, then fetch them."""

        user = UserFactory()
        db.Session.commit()

        bookmarks = BookmarkFactory.create_batch(10, user=user)
        db.Session.commit()

        result = Bookmark.by_user(user.id)
        assert result.count() == 10
