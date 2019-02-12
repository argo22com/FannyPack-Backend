import graphene
from django.contrib.auth import get_user_model
from graphene import relay
from graphene_django import DjangoObjectType, DjangoConnectionField

from .models import Room, Payment, User, Split


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (relay.Node,)


class BalanceType(graphene.ObjectType):
    user = graphene.Field(UserNode, required=True)
    debts = graphene.Float(required=True)
    payments = graphene.Float(required=True)
    balance = graphene.Float(required=True,
        description='Positive = how much the user owes to the room. Negative = user has to get this amount to be fine')


class ResolutionStepType(graphene.ObjectType):
    payer = graphene.Field(UserNode, required=True)
    recipient = graphene.Field(UserNode, required=True)
    amount = graphene.Float(required=True)


class RoomNode(DjangoObjectType):
    class Meta:
        model = Room
        interfaces = (relay.Node,)

    balances = graphene.List(BalanceType, required=True)
    resolution = graphene.List(ResolutionStepType, required=True)

    def resolve_balances(self: Room, info):
        return [BalanceType(**a) for a in self.get_user_balances()]

    def resolve_resolution(self: Room, info):

        return [ResolutionStepType(**a) for a in self.get_resolution()]


class PaymentNode(DjangoObjectType):
    class Meta:
        model = Payment
        interfaces = (relay.Node,)

    amount = graphene.Float(required=True)

    def resolve_amount(self: Payment, info):
        return self.get_amount()


class SplitNode(DjangoObjectType):
    class Meta:
        model = Split
        interfaces = (relay.Node,)


class SplitInputType(graphene.InputObjectType):
    user_id = graphene.GlobalID(parent_type=UserNode, required=True)
    amount = graphene.Float(required=True)


class Outcome(graphene.ObjectType):
    message = graphene.String()


class UserCreateMutation(relay.mutation.ClientIDMutation):
    user = graphene.Field(UserNode)

    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    def mutate_and_get_payload(self, info, username, password, email):
        try:
            user = get_user_model()(
                username=username,
                email=email,
            )
            user.set_password(password)
            user.save()
        except:
            raise Exception('Username or email already exists')

        return UserCreateMutation(user=user)


class RoomCreateMutation(relay.mutation.ClientIDMutation):
    room = graphene.Field(RoomNode)

    class Input:
        name = graphene.String(required=True)
        secret = graphene.String(required=False)

    def mutate_and_get_payload(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')

        room = Room.create_room(kwargs.get('name'), kwargs.get('secret', None))
        return RoomCreateMutation(room=room)


class RoomAddUserMutation(relay.mutation.ClientIDMutation):
    user = graphene.Field(UserNode)

    class Input:
        room_id = graphene.GlobalID(parent_type=RoomNode, required=True)
        user_id = graphene.GlobalID(parent_type=UserNode, required=True)
        secret = graphene.String(required=False)

    def mutate_and_get_payload(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        room: Room = relay.Node.get_node_from_global_id(info, kwargs.get('room_id'), RoomNode)
        user: User = relay.Node.get_node_from_global_id(info, kwargs.get('user_id'), UserNode)

        user.join_room(room, kwargs.get('secret'))
        return RoomAddUserMutation(user)


class PaymentCreateMutation(relay.mutation.ClientIDMutation):
    room = graphene.Field(RoomNode)
    payment = graphene.Field(PaymentNode)

    class Input:
        room_id = graphene.GlobalID(parent_type=RoomNode, required=True)
        pledger_id = graphene.GlobalID(parent_type=UserNode, required=True)
        name = graphene.String(required=True)
        datetime = graphene.DateTime(required=True)
        splits = graphene.List(SplitInputType, required=True)

    def mutate_and_get_payload(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')

        # TODO: check that user is allowed to do so

        room: Room = relay.Node.get_node_from_global_id(info, kwargs.get('room_id'), RoomNode)
        pledger: User = relay.Node.get_node_from_global_id(info, kwargs.get('pledger_id'), UserNode)
        splits = []

        for split in kwargs.get('splits'):
            user: User = relay.Node.get_node_from_global_id(info, split.get('user_id'), UserNode)
            splits.append({
                'user': user,
                'amount': max(split.get('amount'), 0)
            })

        payment = Payment.create_payment(
            room,
            pledger,
            kwargs.get('name'),
            splits,
            kwargs.get('datetime')
        )

        return PaymentCreateMutation(
            room=room,
            payment=payment
        )


class PaymentDeleteMutation(relay.mutation.ClientIDMutation):
    class Input:
        id = graphene.GlobalID(required=True, parent_type=PaymentNode)

    success = graphene.Boolean()
    room = graphene.Field(RoomNode)

    def mutate_and_get_payload(self, info, **kwargs):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')
        payment: Payment = relay.Node.get_node_from_global_id(info, kwargs.get('id'), PaymentNode)
        room = payment.room
        # TODO: check that user is allowed to do so
        payment.delete()
        return PaymentDeleteMutation(success=True, room=room)


class Mutation(graphene.ObjectType):
    user_create = UserCreateMutation.Field()
    room_create = RoomCreateMutation.Field()
    room_add_user = RoomAddUserMutation.Field()
    payment_create = PaymentCreateMutation.Field()
    payment_delete = PaymentDeleteMutation.Field()


class Query(graphene.ObjectType):
    room = relay.Node.Field(RoomNode)
    users = DjangoConnectionField(UserNode)
    me = graphene.Field(UserNode)

    def resolve_users(self, info):
        if info.context.user.is_anonymous:
            raise Exception('Not logged in!')

        return get_user_model().objects.all()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user
