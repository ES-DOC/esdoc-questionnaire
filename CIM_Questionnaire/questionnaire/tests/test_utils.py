__author__ = 'ben.koziol'

from CIM_Questionnaire.questionnaire.tests.base import TestQuestionnaireBase

from CIM_Questionnaire.questionnaire.utils import *

class SampleType(EnumeratedType):
    pass

SampleTypes = EnumeratedTypeList([
    SampleType("ONE","one"),
    SampleType("TWO","two"),
    SampleType("THREE","three"),
])

class FindInSequenceFunction(object):

    n = 0

    @classmethod
    def fn(cls,item,test_value):
        cls.n += 1
        return item == test_value

class Test(TestQuestionnaireBase):

    def setUp(self):
        # no need for all the questionnaire-specific stuff
        #super(Test,self).setUp()
        pass


    def test_find_in_sequence(self):

        test_sequence = [1,2,3,4,5,]

        FindInSequenceFunction.n = 0
        test_item = find_in_sequence(lambda item: FindInSequenceFunction.fn(item,2), test_sequence)
        self.assertEqual(test_item, 2)
        self.assertEqual(FindInSequenceFunction.n, 2)

        FindInSequenceFunction.n = 0
        test_item = find_in_sequence(lambda item: FindInSequenceFunction.fn(item,6), test_sequence)
        self.assertIsNone(test_item)
        self.assertEqual(FindInSequenceFunction.n, len(test_sequence))


    def test_enumerated_types(self):

        # test I can get the right values...
        self.assertEqual(SampleTypes.ONE, "ONE")
        self.assertEqual(SampleTypes.ONE.getType(), "ONE")
        self.assertEqual(SampleTypes.ONE.getName(), "one")

        # test I can't get the wrong values...
        try:
            SampleTypes.FOUR
            self.assertEqual(True, False, msg="failed to recognize invalid enumerated_type")
        except EnumeratedTypeError:
            pass

        # test comparisons work...
        self.assertTrue(SampleTypes.ONE == "ONE")
        self.assertTrue(SampleTypes.ONE != "TWO")

        # although there is support for ordering, I don't actually care


    def test_get_joined_keys_dict(self):
        dct = {u'couplingtechnology_01':
                   {u'couplingtechnology': [],
                    u'implementation': [1, 2, 3, ],
                    u'couplingtechnologykeyproperties': [1, 2, 3, ],
                    u'architecture': [1, ],
                    u'composition': [1, 2, 3, 4, 5, ]},
                u'couplingtechnology_02':
                    {u'couplingtechnology': [99],
                     u'implementation': [10, 20, 30, ],
                    u'couplingtechnologykeyproperties': [10, 20, 30, ],
                    u'architecture': [10, ],
                    u'composition': [10, 20, 30, 40, 50, ]}
            }

        actual = {u'couplingtechnology_01_composition': [1, 2, 3, 4, 5],
                    u'couplingtechnology_02_composition': [10, 20, 30, 40, 50],
                    u'couplingtechnology_02_couplingtechnologykeyproperties': [10, 20, 30],
                    u'couplingtechnology_01_architecture': [1],
                    u'couplingtechnology_01_couplingtechnologykeyproperties': [1, 2, 3],
                    u'couplingtechnology_01_couplingtechnology': [], u'couplingtechnology_02_architecture': [10],
                    u'couplingtechnology_01_implementation': [1, 2, 3],
                    u'couplingtechnology_02_implementation': [10, 20, 30],
                    u'couplingtechnology_02_couplingtechnology': [99]}

        ret = get_joined_keys_dict(dct)

        # output is copied so the memory locations should stay the same
        self.assertEqual(id(ret['couplingtechnology_02_composition']), id(dct['couplingtechnology_02']['composition']))

        self.assertDictEqual(ret, actual)

        # unicode key types are wanted
        for key in ret.iterkeys():
            self.assertIsInstance(key, unicode)