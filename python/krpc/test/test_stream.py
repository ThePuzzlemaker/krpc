#!/usr/bin/env python2

import unittest
import subprocess
import time
import krpc
import krpc.test.Test as TestSchema

class TestStream(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = subprocess.Popen(['bin/TestServer/TestServer.exe', '50001', '50002'])
        time.sleep(0.25)

    def setUp(self):
        self.conn = krpc.connect(name='TestClient', rpc_port=50001, stream_port=50002)

    @classmethod
    def tearDownClass(cls):
        cls.server.kill()

    def test_method(self):
        with self.conn.stream(self.conn.test_service.float_to_string, 3.14159) as x:
            for i in range(5):
                time.sleep(0.1)
                self.assertEqual('3.14159', x())

    def test_property(self):
        self.conn.test_service.string_property = 'foo'
        with self.conn.stream(getattr, self.conn.test_service, 'string_property') as x:
            for i in range(5):
                time.sleep(0.1)
                self.assertEqual('foo', x())

    def test_class_method(self):
        obj = self.conn.test_service.create_test_object('bob')
        with self.conn.stream(obj.float_to_string, 3.14159) as x:
            for i in range(5):
                time.sleep(0.1)
                self.assertEqual('bob3.14159', x())

    def test_class_property(self):
        obj = self.conn.test_service.create_test_object('jeb')
        obj.int_property = 42
        with self.conn.stream(getattr, obj, 'int_property') as x:
            for i in range(5):
                time.sleep(0.1)
                self.assertEqual(42, x())

    def test_property_setters_are_invalid(self):
        self.assertRaises(ValueError, self.conn.add_stream, setattr, self.conn.test_service, 'string_property')
        obj = self.conn.test_service.create_test_object('bill')
        self.assertRaises(ValueError, self.conn.add_stream, setattr, obj.int_property, 42)

    def test_counter(self):
        count = 0
        with self.conn.stream(self.conn.test_service.counter) as x:
            for i in range(5):
                time.sleep(0.1)
                self.assertLess(count, x())
                count = x()

    def test_nested(self):
        with self.conn.stream(self.conn.test_service.float_to_string, 0.123) as x0:
            with self.conn.stream(self.conn.test_service.float_to_string, 1.234) as x1:
                for i in range(5):
                    time.sleep(0.1)
                    self.assertEqual('0.123', x0())
                    self.assertEqual('1.234', x1())

    def test_interleaved(self):
        s0 = self.conn.add_stream(self.conn.test_service.int32_to_string, 0)
        time.sleep(0.1)
        self.assertEqual('0', s0())

        s1 = self.conn.add_stream(self.conn.test_service.int32_to_string, 1)
        time.sleep(0.1)
        self.assertEqual('0', s0())
        self.assertEqual('1', s1())

        s1.remove()
        time.sleep(0.1)
        self.assertEqual('0', s0())
        self.assertRaises(RuntimeError, s1)

        s2 = self.conn.add_stream(self.conn.test_service.int32_to_string, 2)
        time.sleep(0.1)
        self.assertEqual('0', s0())
        self.assertRaises(RuntimeError, s1)
        self.assertEqual('2', s2())

        s0.remove()
        time.sleep(0.1)
        self.assertRaises(RuntimeError, s0)
        self.assertRaises(RuntimeError, s1)
        self.assertEqual('2', s2())

        s2.remove()
        time.sleep(0.1)
        self.assertRaises(RuntimeError, s0)
        self.assertRaises(RuntimeError, s1)
        self.assertRaises(RuntimeError, s2)

    def test_remove_stream_twice(self):
        s = self.conn.add_stream(self.conn.test_service.int32_to_string, 0)
        time.sleep(0.1)
        self.assertEqual('0', s())
        s.remove()
        self.assertRaises(RuntimeError, s)
        s.remove()
        self.assertRaises(RuntimeError, s)

if __name__ == '__main__':
    unittest.main()
