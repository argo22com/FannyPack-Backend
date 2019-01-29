import json
from unittest import TestCase
from payments.utils.optimization import Optimization


class TestOptimization(TestCase):

    def setUp(self):
        self.op = Optimization()
        self.matrix = self.op.create_matrix(['t1', 't2'])

    def test_create_matrix(self):
        users = ['t1', 't2']

        op = Optimization()
        matrix = op.create_matrix(users)

        expected_matrix = {'t1': {'t1': 0.0, 't2': 0.0}, 't2': {'t1': 0.0, 't2': 0.0}}
        self.assertEqual(matrix.to_dict(), expected_matrix)

    def test_create__empty_matrix(self):
        users = []

        op = Optimization()
        matrix = op.create_matrix(users)

        expected_matrix = {}
        self.assertEqual(matrix.to_dict(), expected_matrix)

    def test_add_user(self):
        users = []

        op = Optimization()
        op.create_matrix(users)

        op.add_user('t1')
        expected_matrix = {'t1': {'t1': 0.0}}
        self.assertEqual(op.matrix.to_dict(), expected_matrix)

        op.add_user('t2')
        expected_matrix = {'t1': {'t1': 0.0, 't2': 0.0}, 't2': {'t1': 0.0, 't2': 0.0}}
        self.assertEqual(op.matrix.to_dict(), expected_matrix)

    def test_add_payment_known_user(self):
        self.op.add_payment('t1', 't2', -100)
        expected_matrix = {'t1': {'t1': 100.0, 't2': 0.0}, 't2': {'t1': -100.0, 't2': 0.0}}
        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_add_payment_unknown_user(self):
        self.op.add_payment('t1', 't3', -100)
        expected_matrix = {'t1': {'t1': 100.0, 't2': 0.0, 't3': 0.0},
                           't2': {'t1': 0.0, 't2': 0.0, 't3': 0.0},
                           't3': {'t1': -100.0, 't2': 0.0, 't3': 0.0}}
        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_summarize_matrix(self):
        users = []

        op = Optimization()
        op.create_matrix(users)

        op.add_payment('jirka', 'jirka', 110)
        op.add_payment('Honza', 'jirka', -300)
        op.add_payment('jirka', 'Pavel', -110)
        op.add_payment('jirka', 'Honza', -110)
        expected = [[-80., 0., 0.], [0., 190., 0.], [0., 0., -110.]]
        matrix = op.summarize_matrix()
        self.assertEqual(matrix.tolist(), expected)

    def test_usual_walkthrough(self):
        # j300jph
        self.op.add_payment(drawee='t1', pledger='t1', amount=110)
        self.op.run()
        self.op.add_payment(drawee='t1', pledger='t2', amount=-110)
        self.op.run()
        self.op.add_payment(drawee='t1', pledger='t3', amount=-110)
        self.op.run()

        expected_matrix = {'t1': {'t1': 220.0, 't2': 0.0, 't3': 0.0},
                           't2': {'t1': -110.0, 't2': 0.0, 't3': 0.0},
                           't3': {'t1': -110.0, 't2': 0.0, 't3': 0.0}}

        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_simple_transitions(self):
        # j300jph
        self.op.add_payment(drawee='t1', pledger='t2', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t1', amount=110)
        # h900jph
        self.op.add_payment(drawee='t3', pledger='t1', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t2', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t3', amount=300)
        self.op.run()

        expected_matrix = {'t1': {'t1': 0.0, 't2': 0.0, 't3': -80.0},
                           't2': {'t1': 0.0, 't2': 0.0, 't3': -410.0},
                           't3': {'t1': 0.0, 't2': 0.0, 't3': 490.0}}

        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_one_transition_with_optimization(self):
        self.op.add_payment(drawee='t1', pledger='t2', amount=-110)
        self.op.run()
        expected_matrix = {'t1': {'t1': 110.0, 't2': 0.0}, 't2': {'t1': -110.0, 't2': 0.0}}
        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_advanced_transitions(self):
        # j300jph
        self.op.add_payment(drawee='t1', pledger='t2', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t1', amount=110)
        # h900jph
        self.op.add_payment(drawee='t3', pledger='t1', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t2', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t3', amount=300)
        # p600jph
        self.op.add_payment(drawee='t2', pledger='t1', amount=-200)
        self.op.add_payment(drawee='t2', pledger='t2', amount=200)
        self.op.add_payment(drawee='t2', pledger='t3', amount=-200)
        # j750jph
        self.op.add_payment(drawee='t1', pledger='t1', amount=250)
        self.op.add_payment(drawee='t1', pledger='t2', amount=-250)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-250)
        # t1-250-t4
        self.op.add_payment(drawee='t1', pledger='t4', amount=-250)
        # t4-100-t2
        self.op.add_payment(drawee='t4', pledger='t2', amount=-100)
        self.op.run()

        expected_matrix = {'t1': {'t1': 470.0, 't2': 0.0, 't3': 0.0, 't4': 0.0},
                           't2': {'t1': -360.0, 't2': 0.0, 't3': 0.0, 't4': 0.0},
                           't3': {'t1': 0.0, 't2': 0.0, 't3': 40.0, 't4': 0.0},
                           't4': {'t1': -110.0, 't2': 0.0, 't3': -40.0, 't4': 0.0}}

        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_biggest_pledger(self):
        # j300jph
        self.op.add_payment(drawee='t1', pledger='t2', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-110)
        self.op.add_payment(drawee='t1', pledger='t1', amount=110)
        pledger = self.op.get_biggest_pledger()
        self.assertEqual(pledger, 't2')
        # h900jph
        self.op.add_payment(drawee='t3', pledger='t1', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t2', amount=-300)
        self.op.add_payment(drawee='t3', pledger='t3', amount=300)
        pledger = self.op.get_biggest_pledger()
        self.assertEqual(pledger, 't2')
        # p600jph
        self.op.add_payment(drawee='t2', pledger='t1', amount=-200)
        self.op.add_payment(drawee='t2', pledger='t2', amount=200)
        self.op.add_payment(drawee='t2', pledger='t3', amount=-200)
        pledger = self.op.get_biggest_pledger()
        self.assertEqual(pledger, 't1')
        # j750jph
        self.op.add_payment(drawee='t1', pledger='t1', amount=250)
        self.op.add_payment(drawee='t1', pledger='t2', amount=-250)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-250)
        pledger = self.op.get_biggest_pledger()
        self.assertEqual(pledger, 't2')
        # t1-250-t4
        self.op.add_payment(drawee='t1', pledger='t4', amount=-250)
        # t4-100-t2
        self.op.add_payment(drawee='t4', pledger='t2', amount=-100)
        self.op.run()

        pledger = self.op.get_biggest_pledger()
        self.assertEqual(pledger, 't2')

    def test_simple_float_point_operations(self):

        self.op.add_payment(drawee='t1', pledger='t2', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t1', amount=33.33333)
        expected_matrix = {'t1': {'t1': 66.66, 't2': 0.0, 't3': 0.0},
                           't2': {'t1': -33.33, 't2': 0.0, 't3': 0.0},
                           't3': {'t1': -33.33, 't2': 0.0, 't3': 0.0}}
        self.assertEqual(self.op.matrix.to_dict(), expected_matrix)

    def test_float_point_operations(self):

        self.op.add_payment(drawee='t1', pledger='t2', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t1', amount=33.33333)
        self.op.add_payment(drawee='t1', pledger='t2', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t1', amount=33.33333)
        self.op.add_payment(drawee='t1', pledger='t2', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t1', amount=33.33333)
        self.op.add_payment(drawee='t1', pledger='t2', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t3', amount=-33.33333)
        self.op.add_payment(drawee='t1', pledger='t1', amount=33.33333)

        expected_matrix = {'t1': {'t1': 266.64, 't2': 0.0, 't3': 0.0},
                           't2': {'t1': -133.32, 't2': 0.0, 't3': 0.0},
                           't3': {'t1': -133.32, 't2': 0.0, 't3': 0.0}}
        self.op.run()
        stringified = self.op.export_to_json()
        dict = json.loads(stringified)
        self.assertEqual(dict, expected_matrix)
