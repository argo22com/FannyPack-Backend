from django.contrib.auth.models import User
from django.test import TestCase

from payments.models import Room, Payment


# Create your tests here.
class TestRoomsModel(TestCase):

    def test_create_room(self):
        room = Room.create_room("test")
        self.assertEqual(room.matrix, "{}")

    def test_add_user(self):
        room = Room.create_room("test")
        user = User(username="t_user", password="test", email="test@test.test")
        user2 = User(username="t_user2", password="test", email="test@test.test")
        user.save()
        user2.save()
        room.add_user(user)
        self.assertEqual(room.matrix, '{"t_user":{"t_user":0.0}}')
        room.add_user(user2)
        self.assertEqual(room.matrix, '{"t_user":{"t_user":0.0,"t_user2":0.0},'
                                      '"t_user2":{"t_user":0.0,"t_user2":0.0}}')


class TestPayments(TestCase):
    def setUp(self):
        self.room = Room.create_room("test_payment")
        self.user = User(username="t_user", password="test", email="test@test.test")
        self.user2 = User(username="t_user2", password="test", email="test@test.test")
        self.user.save()
        self.user2.save()
        self.room.add_user(self.user)
        self.room.add_user(self.user2)

    def test_payment(self):
        outcome = Payment.create_payment(drawee=self.user.username,
                                         pledger=self.user2.username,
                                         amount=-125.0,
                                         room="test_payment",
                                         name="test_payment")

        self.assertEqual(outcome['matrix'].matrix, '{"t_user":{"t_user":125.0,"t_user2":0.0},'
                                                   '"t_user2":{"t_user":-125.0,"t_user2":0.0}}')

    def test_delete_payment(self):
        outcome = Payment.create_payment(drawee=self.user.username,
                                         pledger=self.user2.username,
                                         amount=-125.0,
                                         room="test_payment",
                                         name="test_payment")
        payment_id = outcome['payment'].id

        self.assertEqual(Payment.objects.count(), 1)

        Payment.delete_payment(payment_id)

        self.assertEqual(Payment.objects.count(), 0)

    def test_delete_payment_integrity_check(self):
        outcome = Payment.create_payment(drawee=self.user.username,
                                         pledger=self.user2.username,
                                         amount=-125.0,
                                         room="test_payment",
                                         name="test_payment")

        matrix = Room.objects.get(name="test_payment").matrix

        self.assertEqual(matrix, '{"t_user":{"t_user":125.0,"t_user2":0.0},'
                                 '"t_user2":{"t_user":-125.0,"t_user2":0.0}}')

        Payment.delete_payment_keep_integrity(outcome['payment'].id)

        matrix = Room.objects.get(name="test_payment").matrix
        self.assertEqual(matrix, '{"t_user":{"t_user":0.0,"t_user2":0.0},'
                                 '"t_user2":{"t_user":0.0,"t_user2":0.0}}')

    # def test_create_review(self):
    #     client = Client(schema)
    #
    #     message = "what's uuuuupp?!"
    #
    #     review = f"""
    #         mutation{{
    #          createReview(text: "{message}") {{
    #             review {{
    #             author{{
    #                 username
    #             }}
    #             text
    #             createdAt
    #             }}
    #          }}
    #         }}
    #     """
    #
    #     request = RequestFactory()
    #     request.user = User.objects.create_user(
    #         username='jacob', email='jacob@…', password='top_secret')
    #     executed = client.execute(review, context=request)
    #     self.assertEqual(executed['data']['createReview']['review']['text'], message)
    #     self.assertEqual(executed['data']['createReview']['review']['author']['username'], 'jacob')
    #
    # def test_hey(self):
    #     client = Client(schema)
    #
    #     mutation = """
    #     mutation {
    #      createUser(username: "test", password: "test", email: "testmail"){
    #         user{
    #             username
    #         }
    #      }
    #     }
    #     """
    #
    #     mutate = client.execute(mutation)
    #
    #     query = """
    #     query {
    #      users{
    #         id
    #         username
    #      }
    #     }
    #     """
    #     with captured_stderr():
    #         executed = client.execute(query)
    #
    #     tokenMutation = """
    #     mutation
    #     {
    #         tokenAuth(username: "test", password: "test"){
    #         token
    #     }
    #     }
    #     """
    #     executed = client.execute(tokenMutation)
    #     token = "JWT %s" % executed['data']['tokenAuth']['token']
    #
    #     createOrderMutation = """
    #     mutation
    #     {
    #         createOrder(name: "testOrder", cost: 50, date: "2018-11-15")
    #     {
    #         order
    #     {
    #         name
    #     }
    #     }
    #     }
    #     """
    #
    #     executed = client.execute(createOrderMutation, context={"headers": {"Authorization": "JWT "+token}})
    #
    #     self.assertEqual(executed['data']['users'][0]['username'], "test")
