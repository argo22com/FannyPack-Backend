import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import transaction

from payments.utils.optimization import Optimization
from fannypack import settings

from payments.utils.secretManager import check_password, hash_password


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    matrix = models.TextField()
    total_balance = models.FloatField(default=0.0)
    biggest_pledger = models.CharField(max_length=30)
    secret = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def create_room(name, secret=None):
        if secret is not None:
            room = Room(
                name=name,
                secret=hash_password(secret)
            )
        else:
            room = Room(
                name=name
            )

        op = Optimization()
        op.create_matrix([])
        room.matrix = op.export_to_json()
        room.save()
        return room

    @staticmethod
    def update_matrix(room_id, matrix):
        try:
            db_room = Room.objects.get(id=room_id)
            db_room.matrix = matrix
            db_room.save()
            return db_room
        except Exception:
            raise Exception("room doesn't exist")

    def add_payment(self, payment):
        self.total_balance += abs(payment)
        op = Optimization()
        op.load_from_json(self.matrix)
        self.biggest_pledger = op.get_biggest_pledger()
        self.save()

    def add_user(self, user):
        op = Optimization()
        op.load_from_json(self.matrix)
        op.add_user(user.username)
        self.matrix = op.export_to_json()
        self.save()
        return self


class User(AbstractUser):
    balance = models.DecimalField(default=0, decimal_places=5, max_digits=20)
    rooms = models.ManyToManyField(Room)

    def add_user_to_room(self, room_id, secret=None):
        try:
            room = Room.objects.get(id=room_id)
            if room.secret:
                if secret is None:
                    raise Exception("Room is protected by password")
                if not check_password(room.secret, secret):
                    raise Exception("Incorrect password")
            room.add_user(self)
            self.rooms.add(room)
            self.save()
        except models.FieldDoesNotExist:
            raise Exception("room doesn't exist")

    def update_balance(self, value):
        print(self.balance)
        self.balance += Decimal(str(value))
        self.save()


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drawee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Drawee")
    pledger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Pledger")
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=50)

    @staticmethod
    @transaction.atomic
    def create_payment(drawee, pledger, room_id, amount, name):
        try:
            drawee = User.objects.get(username=drawee)
            pledger = User.objects.get(username=pledger)
            room_model = Room.objects.get(id=room_id)
        except models.FieldDoesNotExist:
            raise Exception("payments fields doesn't exist")

        payment = Payment.objects.create(
            drawee=drawee,
            pledger=pledger,
            room=room_model,
            amount=amount,
            name=name,
        )

        try:
            op = Optimization()
            op.load_from_json(room_model.matrix)
            op.add_payment(drawee=drawee, pledger=pledger, amount=float(amount))
            op.run()
            matrix = op.export_to_json()

            updated_room = Room.update_matrix(room_id=room_id, matrix=matrix)
            updated_room.add_payment(amount)

            drawee.update_balance(-amount)
            pledger.update_balance(amount)

            payment.save()
        except Exception:
            payment.delete()
            return

        return {'payment': payment, 'matrix': updated_room}

    @staticmethod
    def delete_payment(id: int):
        Payment.objects.get(id=id).delete()

    @staticmethod
    def delete_payment_keep_integrity(id: int):
        payment = Payment.objects.get(id=id)
        room = Room.objects.get(id=payment.room.id)
        room.total_balance -= abs(2 * payment.amount)
        room.save()

        inverted_payment = Payment.create_payment(
            payment.pledger,
            payment.drawee,
            payment.room_id,
            payment.amount,
            payment.name,
        )

        inverted_payment['payment'].delete()
        payment.delete()

