import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType

from .models import Room, Payment, User


class UserType(DjangoObjectType):
    class Meta:
        model = User


class RoomType(DjangoObjectType):
    class Meta:
        model = Room


class PaymentType(DjangoObjectType):
    class Meta:
        model = Payment


class Outcome(graphene.ObjectType):
    message = graphene.String()


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate(self, info, username, password, email):
        user = get_user_model()(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)


class CreateRoom(graphene.Mutation):
    room = graphene.Field(RoomType)

    class Arguments:
        name = graphene.String(required=True)
        secret = graphene.String(required=False)

    def mutate(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        if not kwargs.get('secret') or kwargs.get('secret') is '':
            room = Room.create_room(kwargs.get('name'))
        else:
            room = Room.create_room(kwargs.get('name'), kwargs.get('secret'))
        return CreateRoom(room)


class AddUserToRoom(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        room_id = graphene.String(required=True)
        username = graphene.String(required=True)
        secret = graphene.String(required=False)

    def mutate(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        user = User.objects.get(username=kwargs.get("username"))
        if kwargs.get('secret'):
            user.add_user_to_room(kwargs.get("room_id"), kwargs.get('secret'))
        else:
            user.add_user_to_room(kwargs.get("room_id"))
        return AddUserToRoom(user)


class MakePayment(graphene.Mutation):
    matrix = graphene.Field(RoomType)
    payment = graphene.Field(PaymentType)

    class Arguments:
        drawee = graphene.String(required=True)
        pledger = graphene.String(required=True)
        room_id = graphene.String(required=True)
        amount = graphene.Float(required=True)
        name = graphene.String(required=True)

    def mutate(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        payment = Payment.create_payment(**kwargs)
        return MakePayment(payment['matrix'], payment['payment'])


class DeletePayment(graphene.Mutation):
    class Arguments:
        id = graphene.String(required=True)

    Output = Outcome

    def mutate(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        Payment.delete_payment_keep_integrity(**kwargs)
        outcome_message = "Payment " + kwargs.get('id') + " was deleted"
        return Outcome(message=outcome_message)


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    create_room = CreateRoom.Field()
    add_user_to_room = AddUserToRoom.Field()
    make_payment = MakePayment.Field()
    delete_payment = DeletePayment.Field()


class Query(graphene.ObjectType):
    room = graphene.Field(RoomType, room_id=graphene.String())
    get_rooms = graphene.List(RoomType)
    get_payments = graphene.List(PaymentType, room_id=graphene.String())
    users = graphene.List(UserType, room_id=graphene.String(required=False))
    me = graphene.Field(UserType)

    def resolve_users(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')

        if kwargs.get('room_id'):
            return get_user_model().objects.filter(rooms__id=kwargs.get('room_id'))
        return get_user_model().objects.all()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user

    def resolve_room(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        room = Room.objects.get(id=kwargs.get('room_id'))
        return room

    def resolve_get_rooms(self, info):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        return Room.objects.all()

    def resolve_get_payments(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        return Payment.objects.filter(room__id=kwargs.get('room_id')).order_by('-date')[:10]
