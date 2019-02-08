import factory
from .. import db
from ..model.bookmark import Bookmark, Tag, Link
from ..model.user import User


class SQLAlchemyGetOrCreateOptions(factory.alchemy.SQLAlchemyOptions):
    def _build_default_options(self):
        return super(SQLAlchemyGetOrCreateOptions, self)._build_default_options() + [
            factory.base.OptionDefault("sqlalchemy_get_or_create", (), inherit=True)
        ]


class SQLAlchemyGetOrCreateModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    _options_class = SQLAlchemyGetOrCreateOptions

    @classmethod
    def _get_or_create(cls, model_class, *args, **kwargs):
        session = cls._meta.sqlalchemy_session
        if session is None:
            raise RuntimeError("No session provided.")

        filters = {}
        for field in cls._meta.sqlalchemy_get_or_create:
            if field not in kwargs:
                # TODO: should be factory.errors.FactoryError
                raise RuntimeError(
                    "Unable to find initialization value for '%s' in factory %s"
                    % (field, cls.___name__)
                )

            filters[field] = kwargs[field]

        with session.no_autoflush:
            return session.query(model_class).filter_by(**filters).one_or_none()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if cls._meta.sqlalchemy_get_or_create:
            obj = cls._get_or_create(model_class, *args, **kwargs)
            if obj is not None:
                return obj

        return super(SQLAlchemyGetOrCreateModelFactory, cls)._create(model_class, *args, **kwargs)


# https://factoryboy.readthedocs.io/en/latest/reference.html#inheritance According to the
# documentation the sequence counter *won't* be shared across children classes since they do not
# share the same model as their parent class.
class BaseModelFactory(SQLAlchemyGetOrCreateModelFactory):
    class Meta:
        sqlalchemy_session = db.Session


class UserFactory(BaseModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "{}{}".format(factory.Faker("user_name"), n))
    email = factory.LazyAttribute(lambda obj: "{.username}@example.com".format(obj))
    display_name = factory.Faker("name")
    password = factory.Faker("password")
    active = True
    admin = False


class TagFactory(BaseModelFactory):
    class Meta:
        model = Tag
        sqlalchemy_get_or_create = ("name",)

    name = factory.Sequence(lambda n: "{}{}".format(factory.Faker("word"), n))


class LinkFactory(BaseModelFactory):
    class Meta:
        model = Link

    href = factory.Sequence(lambda n: "{}?foo={}".format(factory.Faker("uri"), n))


class BookmarkFactory(BaseModelFactory):
    class Meta:
        model = Bookmark

    title = factory.Faker("sentence", nb_words=6)
    notes = factory.Faker("text")
    private = False
    # tags = factory.SubFactory(TagFactory)
    # href = factory.SubFactory(LinkFactory)
    # user = factory.SubFactory(UserFactory)

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
                self.tags.append(tag)

    @factory.post_generation
    def link(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.link = extracted
        else:
            # let's provide a default for the link
            self.link = LinkFactory.create()
