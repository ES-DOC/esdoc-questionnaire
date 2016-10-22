# ####################
# #   ES-DOC CIM Questionnaire
# #   Copyright (c) 2016 ES-DOC. All rights reserved.
# #
# #   University of Colorado, Boulder
# #   http://cires.colorado.edu/
# #
# #   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
# ####################
#
# __author__ = "allyn.treshansky"
#
# """
# .. module:: test_views_services_document_publish
#
# """
#
# from django.core.urlresolvers import reverse
# from django.conf import settings
#
# from Q.questionnaire.q_utils import FuzzyInt, add_parameters_to_url
# from Q.questionnaire.tests.test_base import TestQBase, TEST_AJAX_REQUEST
# from Q.questionnaire.models.models_projects import QProject
# from Q.questionnaire.models.models_realizations_bak import MetadataModel
# from Q.questionnaire.views.services.views_services_document_publish import *
#
# class Test(TestQBase):
#
#     # test written for issue #425...
#     def test_document_publish_modification_time(self):
#
#         original_test_documents = MetadataModel.objects.filter(project__name__iexact="esps", is_document=True, is_root=True)
#         original_modification_dates = [td.last_modified for td in original_test_documents]
#
#         test_document = original_test_documents[0]
#         self.assertEqual(test_document.is_complete(), True)
#
#         response = self.client.post(
#             reverse("document_publish"),
#             data={
#                 "document_id": test_document.pk,
#             },
#             **TEST_AJAX_REQUEST
#         )
#
#         new_test_documents = MetadataModel.objects.filter(project__name__iexact="esps", is_document=True, is_root=True)
#         new_modification_dates = [td.last_modified for td in new_test_documents]
#
#         for i, (original_modification_date, new_modification_date) in enumerate(zip(original_modification_dates, new_modification_dates)):
#             if i == 0:
#                 self.assertGreater(new_modification_date, original_modification_date)
#             else:
#                 self.assertEqual(new_modification_date, original_modification_date)
#
#
