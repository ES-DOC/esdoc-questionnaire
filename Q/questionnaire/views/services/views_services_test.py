####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2017 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

from django.http import HttpResponseForbidden, JsonResponse
from Q.questionnaire.views.services.views_services_base import validate_request

# TEST_DATA = {
#     "id": 2,
#     "name": "model",
#     "description": "",
#     "version": "1.2.0",
#     "owner": 1,
#     "shared_owners": [
#
#     ],
#     "properties": [
#         {
#             "id": 7,
#             "name": "name",
#             "proxy": 1,
#             "order": 1,
#             "field_type": "ATOMIC",
#             "cardinality": "1|1",
#             "atomic_value": "my test",
#             "enumeration_value": "",
#             "enumeration_other_value": None,
#             "relationship_values": [
#
#             ],
#             "is_nil": False,
#             "nil_reason": "UNKNOWN",
#             "is_complete": True,
#             "key": "63a63777-0267-4e02-8dce-3b4e2765643c",
#             "is_multiple": False,
#             "is_required": True,
#             "possible_relationship_targets": [
#
#             ],
#             "display_detail": False
#         },
#         {
#             "id": 8,
#             "name": "enumeration",
#             "proxy": 2,
#             "order": 2,
#             "field_type": "ENUMERATION",
#             "cardinality": "0|1",
#             "atomic_value": None,
#             "enumeration_value": "one",
#             "enumeration_other_value": None,
#             "relationship_values": [
#
#             ],
#             "is_nil": False,
#             "nil_reason": "UNKNOWN",
#             "is_complete": True,
#             "key": "e5e7bee7-ee7d-45c9-b172-2aa76cdc13ea",
#             "is_multiple": False,
#             "is_required": False,
#             "possible_relationship_targets": [
#
#             ],
#             "display_detail": False
#         },
#         {
#             "id": 9,
#             "name": "thing",
#             "proxy": 3,
#             "order": 3,
#             "field_type": "RELATIONSHIP",
#             "cardinality": "0|1",
#             "atomic_value": None,
#             "enumeration_value": "",
#             "enumeration_other_value": None,
#             "relationship_values": [
#                 {
#                     "id": 4,
#                     "name": "recursive_thing",
#                     "description": "",
#                     "version": "1.2.0",
#                     "owner": None,
#                     "shared_owners": [
#
#                     ],
#                     "properties": [
#                         {
#                             "id": 14,
#                             "name": "name",
#                             "proxy": 4,
#                             "order": 1,
#                             "field_type": "ATOMIC",
#                             "cardinality": "1|1",
#                             "atomic_value": None,
#                             "enumeration_value": "",
#                             "enumeration_other_value": None,
#                             "relationship_values": [
#
#                             ],
#                             "is_nil": False,
#                             "nil_reason": "UNKNOWN",
#                             "is_complete": False,
#                             "key": "cc724be8-0b26-49db-b23c-4b71169e4eaf",
#                             "is_multiple": False,
#                             "is_required": True,
#                             "possible_relationship_targets": [
#
#                             ],
#                             "display_detail": False
#                         },
#                         {
#                             "id": 15,
#                             "name": "child",
#                             "proxy": 5,
#                             "order": 2,
#                             "field_type": "RELATIONSHIP",
#                             "cardinality": "0|*",
#                             "atomic_value": None,
#                             "enumeration_value": "",
#                             "enumeration_other_value": None,
#                             "relationship_values": [
#                                 {
#                                     "id": 5,
#                                     "name": "recursive_thing",
#                                     "description": "",
#                                     "version": "1.2.0",
#                                     "owner": None,
#                                     "shared_owners": [
#
#                                     ],
#                                     "properties": [
#                                         {
#                                             "id": 17,
#                                             "name": "name",
#                                             "proxy": 4,
#                                             "order": 1,
#                                             "field_type": "ATOMIC",
#                                             "cardinality": "1|1",
#                                             "atomic_value": "one",
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": True,
#                                             "key": "e7c036fb-dc41-4820-9244-7a3d7775215e",
#                                             "is_multiple": False,
#                                             "is_required": True,
#                                             "possible_relationship_targets": [
#
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 18,
#                                             "name": "child",
#                                             "proxy": 5,
#                                             "order": 2,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|*",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "3cce1fe4-96c3-4bab-b651-82855adc347d",
#                                             "is_multiple": True,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 2,
#                                                     "name": "recursive_thing"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 19,
#                                             "name": "multiple_targets",
#                                             "proxy": 6,
#                                             "order": 3,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|1",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "871ffc9c-25fb-463d-8dc0-be917e122ad6",
#                                             "is_multiple": False,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 3,
#                                                     "name": "other_thing_one"
#                                                 },
#                                                 {
#                                                     "pk": 4,
#                                                     "name": "other_thing_two"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         }
#                                     ],
#                                     "project": 1,
#                                     "ontology": 1,
#                                     "proxy": 2,
#                                     "is_document": False,
#                                     "is_root": False,
#                                     "is_published": False,
#                                     "is_active": True,
#                                     "is_complete": False,
#                                     "key": "69247bbf-c4db-40cb-9847-03bffedfb5a5",
#                                     "display_detail": False,
#                                     "display_properties": False
#                                 },
#                                 {
#                                     "id": 6,
#                                     "name": "recursive_thing",
#                                     "description": "",
#                                     "version": "1.2.0",
#                                     "owner": None,
#                                     "shared_owners": [
#
#                                     ],
#                                     "properties": [
#                                         {
#                                             "id": 20,
#                                             "name": "name",
#                                             "proxy": 4,
#                                             "order": 1,
#                                             "field_type": "ATOMIC",
#                                             "cardinality": "1|1",
#                                             "atomic_value": "two",
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": True,
#                                             "key": "c1354d64-d846-46e7-bc33-7ec23b060b76",
#                                             "is_multiple": False,
#                                             "is_required": True,
#                                             "possible_relationship_targets": [
#
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 21,
#                                             "name": "child",
#                                             "proxy": 5,
#                                             "order": 2,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|*",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "61915f58-3607-4c8e-9191-39bf3f9b0069",
#                                             "is_multiple": True,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 2,
#                                                     "name": "recursive_thing"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 22,
#                                             "name": "multiple_targets",
#                                             "proxy": 6,
#                                             "order": 3,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|1",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "b01eaed5-9b82-47a2-9cc7-31024298cc3b",
#                                             "is_multiple": False,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 3,
#                                                     "name": "other_thing_one"
#                                                 },
#                                                 {
#                                                     "pk": 4,
#                                                     "name": "other_thing_two"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         }
#                                     ],
#                                     "project": 1,
#                                     "ontology": 1,
#                                     "proxy": 2,
#                                     "is_document": False,
#                                     "is_root": False,
#                                     "is_published": False,
#                                     "is_active": True,
#                                     "is_complete": False,
#                                     "key": "300ade30-6c7f-4adc-b217-1ba3d8f8dbe8",
#                                     "display_detail": False,
#                                     "display_properties": False
#                                 },
#                                 {
#                                     "id": 7,
#                                     "name": "recursive_thing",
#                                     "description": "",
#                                     "version": "1.2.0",
#                                     "owner": None,
#                                     "shared_owners": [
#
#                                     ],
#                                     "properties": [
#                                         {
#                                             "id": 23,
#                                             "name": "name",
#                                             "proxy": 4,
#                                             "order": 1,
#                                             "field_type": "ATOMIC",
#                                             "cardinality": "1|1",
#                                             "atomic_value": "three",
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": True,
#                                             "key": "e3947772-1522-4369-8f14-9e7fa59d8ac7",
#                                             "is_multiple": False,
#                                             "is_required": True,
#                                             "possible_relationship_targets": [
#
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 24,
#                                             "name": "child",
#                                             "proxy": 5,
#                                             "order": 2,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|*",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "004636e9-c029-4c4f-a060-49298f454150",
#                                             "is_multiple": True,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 2,
#                                                     "name": "recursive_thing"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         },
#                                         {
#                                             "id": 25,
#                                             "name": "multiple_targets",
#                                             "proxy": 6,
#                                             "order": 3,
#                                             "field_type": "RELATIONSHIP",
#                                             "cardinality": "0|1",
#                                             "atomic_value": None,
#                                             "enumeration_value": "",
#                                             "enumeration_other_value": None,
#                                             "relationship_values": [
#
#                                             ],
#                                             "is_nil": False,
#                                             "nil_reason": "UNKNOWN",
#                                             "is_complete": False,
#                                             "key": "e7ce05a8-0958-4b76-b1f9-c60b7aff3ea7",
#                                             "is_multiple": False,
#                                             "is_required": False,
#                                             "possible_relationship_targets": [
#                                                 {
#                                                     "pk": 3,
#                                                     "name": "other_thing_one"
#                                                 },
#                                                 {
#                                                     "pk": 4,
#                                                     "name": "other_thing_two"
#                                                 }
#                                             ],
#                                             "display_detail": False
#                                         }
#                                     ],
#                                     "project": 1,
#                                     "ontology": 1,
#                                     "proxy": 2,
#                                     "is_document": False,
#                                     "is_root": False,
#                                     "is_published": False,
#                                     "is_active": True,
#                                     "is_complete": False,
#                                     "key": "b9f3c966-33de-4d00-b213-fedafae2ff71",
#                                     "display_detail": False,
#                                     "display_properties": False
#                                 }
#                             ],
#                             "is_nil": False,
#                             "nil_reason": "UNKNOWN",
#                             "is_complete": False,
#                             "key": "8226358a-e8f3-4675-948f-a8cc64a43d28",
#                             "is_multiple": True,
#                             "is_required": False,
#                             "possible_relationship_targets": [
#                                 {
#                                     "pk": 2,
#                                     "name": "recursive_thing"
#                                 }
#                             ],
#                             "display_detail": False
#                         },
#                         {
#                             "id": 16,
#                             "name": "multiple_targets",
#                             "proxy": 6,
#                             "order": 3,
#                             "field_type": "RELATIONSHIP",
#                             "cardinality": "0|1",
#                             "atomic_value": None,
#                             "enumeration_value": "",
#                             "enumeration_other_value": None,
#                             "relationship_values": [
#
#                             ],
#                             "is_nil": False,
#                             "nil_reason": "UNKNOWN",
#                             "is_complete": False,
#                             "key": "a414e8f4-a87f-4c9c-a4c2-bed0e58a2032",
#                             "is_multiple": False,
#                             "is_required": False,
#                             "possible_relationship_targets": [
#                                 {
#                                     "pk": 3,
#                                     "name": "other_thing_one"
#                                 },
#                                 {
#                                     "pk": 4,
#                                     "name": "other_thing_two"
#                                 }
#                             ],
#                             "display_detail": False
#                         }
#                     ],
#                     "project": 1,
#                     "ontology": 1,
#                     "proxy": 2,
#                     "is_document": False,
#                     "is_root": False,
#                     "is_published": False,
#                     "is_active": True,
#                     "is_complete": False,
#                     "key": "65122ec7-a65c-4909-85a1-3e5b1c4f737d",
#                     "display_detail": False,
#                     "display_properties": False
#                 }
#             ],
#             "is_nil": False,
#             "nil_reason": "UNKNOWN",
#             "is_complete": True,
#             "key": "c8e937a1-19d4-41eb-b8b2-90f2651455fc",
#             "is_multiple": False,
#             "is_required": False,
#             "possible_relationship_targets": [
#                 {
#                     "pk": 2,
#                     "name": "recursive_thing"
#                 }
#             ],
#             "display_detail": False
#         }
#     ],
#     "project": 1,
#     "ontology": 1,
#     "proxy": 1,
#     "is_document": True,
#     "is_root": True,
#     "is_published": True,
#     "is_active": True,
#     "is_complete": True,
#     "key": "652bb84c-493b-415e-8b5e-11e7530b9894",
#     "display_detail": False,
#     "display_properties": False
# }


TEST_DATA = {
  "id": None,
  "version": "1.2.0",
  "name": "top-level model",
  "documentation": "some documentation",
  "label": None,
  "proxy": 1,
  "proxy_type": "model",
  "project": 1,
  "owner": 1,
  "shared_owners": [

  ],
  "is_meta": True,
  "is_root": True,
  "is_active": True,
  "is_published": False,
  "is_complete": True,
  "key": "652bb84c-493b-415e-8b5e-11e7530b9894",
  "display_detail": False,
  "display_properties": False,
  "properties": [

  ],
  "nodes": [
      {
        "id": None,
        "version": "1.2.0",
        "name": "atmosphere",
        "documentation": "some documentation",
        "label": None,
        "proxy": 1,
        "proxy_type": "realm",
        "project": 1,
        "owner": 1,
        "shared_owners": [

        ],
        "is_meta": True,
        "is_root": False,
        "is_active": True,
        "is_published": False,
        "is_complete": True,
        "key": "652bb84c-493b-415e-8b5e-11e7530b9894",
        "display_detail": False,
        "display_properties": False,
        "properties": [

        ],
        "nodes": [

        ]
      }
  ]
}

def q_services_test(request):

    valid_request, msg = validate_request(request, valid_methods=["GET"])
    if not valid_request:
        return HttpResponseForbidden(msg)

    return JsonResponse(TEST_DATA, safe=False)
