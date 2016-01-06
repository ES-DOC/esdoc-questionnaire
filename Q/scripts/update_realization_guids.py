####################
#   ES-DOC CIM Questionnaire
#   Copyright (c) 2016 ES-DOC. All rights reserved.
#
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__ = "allyn.treshansky"

"""
stand-alone script to update the guids used to identify realizations & publications
required after the major v0.15.0.0 refactoring
to ensure that previously published models were not re-ingested into the ES-DOC archive
"""

import django
import sys
import os

rel = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# a bit of hackery to get this to run outside of the manage.py script
sys.path.append(rel(".."))  # note that "/scripts" is 1 directory below the project settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
# now I can do Django & Questionnaire stuff...

# TODO: RATHER THAN HARD-CODE THIS
# TODO: TAKE IT AS SCRIPT INPUT

GUIDS_BY_PROJECT = {
    "esps": [
        {"label": "CAM", "guid": "f158d460-b3e7-4db4-ad37-e5a1e22107a3", },
        {"label": "CICE", "guid": "66c108dc-e9ea-4aac-a54d-a0311a3322e1", },
        {"label": "COAMPS Atmosphere", "guid": "8cec115c-7440-4834-b84f-df9b62550ee3", },
        {"label": "FIM", "guid": "5891d44e-2efb-46b3-928a-992d4326a08c", },
        {"label": "GEOS-5 atmosphere", "guid": "93ab6cf7-14b3-4a29-9340-32f42bd92fd2", },
        {"label": "GSM", "guid": "5f2b1b5b-15a4-4bfb-b4cc-b670dbed33d6", },
        {"label": "HYCOM", "guid": "a362e050-bb13-4c3b-8e06-35077709bbc3", },
        {"label": "KISS", "guid": "d28394c4-5713-4841-be17-3aff6a563a4d", },
        {"label": "ModelE atmosphere", "guid": "f4b07b32-ac99-4db9-93dd-180e540cffbe", },
        {"label": "MOM", "guid": "1fc78771-45c5-4eff-a494-c36c1aee7cd4", },
        {"label": "NavGEM", "guid": "5e19d55b-e4a9-4ad4-8fe6-d83361428a8d", },
        {"label": "NCOM", "guid": "fe46dd56-62ff-4f5d-92f4-3d73c2bd1042", },
        {"label": "Neptune", "guid": "fc6da8c0-a8e7-41bc-bee3-4e03720fef16", },
        {"label": "POM", "guid": "91c3cd0d-ec3d-4e06-a4cd-1c52281566c1", },
        {"label": "POP", "guid": "44b1d34e-52e9-4667-be10-992dec4c0b62", },
        {"label": "NMMB", "guid": "434df155-1c0a-494e-9ac6-89d1760a9354", },
        {"label": "SWAN", "guid": "1ef7fe19-2fe1-45dc-b3a0-a274e68c89dd", },
        {"label": "WaveWatch III", "guid": "58317588-dbcd-47e3-939b-7ab3ec65de01", },
        {"label": "WRF", "guid": "a68e2761-ad4b-4d08-8b20-c2e62d75c636", },
        {"label": "MPAS-O", "guid": "26fd36dd-2ff7-4b77-80ed-16cdfb5639e2", },
    ],
    "es-fdl": [
        {"label": "ESMF (Rocky)", "guid": "b45d6a72-4337-4320-87ab-c5ffe5b2a42b", },
        # ...other es-fdl realizations were only ever for testing
    ],
    "downscaling": [
        {"label": "arrmv1-gridded", "guid": "f4b3dfaa-c816-40bb-9ce4-cbcb340306a6", },
        # ...other downscaling realizations were never published
    ],
    "dycore": [
        {"label": 'CAM-FV2', "guid": "fa93486e-d86c-4dd1-90c1-2fd8bd28d8c1", },
        {"label": 'CAM-SE', "guid": "14cced5a-fd01-42da-af84-67003bd404a1", },
        {"label": 'PUMA', "guid": "f753f67e-177f-466c-81e9-ea102505530a", },
        {"label": 'DYNAMICO', "guid": "17255f1c-2168-4fae-9c0d-216b3c998469", },
        {"label": 'ENDGame', "guid": "132609e8-66a0-4e7c-a83f-f6d377596ff2", },
        {"label": 'FIM', "guid": "748331ee-04f9-455a-87e0-eaabef5128ea", },
        {"label": 'mcore', "guid": "5d3a022d-4b02-4268-8ed4-a0d652facc87", },
        {"label": 'fv3-gfdl', "guid": "9b16fb7a-e4f9-4323-9636-ca85d8c5625c", },
        {"label": 'GEM-yinyang', "guid": "6c5a9ed5-b4b1-4a41-b42d-9ef8561416d9", },
        {"label": 'GEM-latlon', "guid": "16c5a1f2-31e0-4e66-a90a-aa27b5de2540", },
        {"label": 'IFS', "guid": "a299c73e-2ea0-44a3-a8f3-0ea8884aef44", },
        {"label": 'ICON-IAP', "guid": "80992011-b028-4746-ade3-7131f8df2b5a", },
        {"label": 'ICON-MPI-DWD', "guid": "a52d396f-7e00-479b-8dbe-660518648d9b", },
        {"label": 'MPAS', "guid": "4bd04760-1240-4112-8495-35ebe8dd4cf9", },
        {"label": 'NICAM', "guid": "96d8e181-6d34-4bcf-b61b-7d562bea9522", },
        {"label": 'NIM', "guid": "bc98f751-45ca-429d-bf8c-aaaee750bc88", },
        {"label": 'OLAM', "guid": "97029360-2dad-4f27-a208-83c60bac66f7", },
        {"label": 'UZIM', "guid": "f6414981-9679-40a3-8ca8-8fff1b8c01ab", },
    ],
}

from lxml import etree as et
from lxml.etree import XMLSyntaxError
from Q.questionnaire.models import *
from Q.questionnaire.models.models_publications import QPublicationFormats
from Q.questionnaire.q_utils import find_in_sequence, get_index

for project_name, guid_dictionaries in GUIDS_BY_PROJECT.iteritems():
    project = QProject.objects.get(name=project_name)
    realizations = MetadataModel.objects.filter(project=project, is_document=True, is_root=True)
    for guid_dictionary in guid_dictionaries:
        label = guid_dictionary["label"]
        guid = guid_dictionary["guid"]
        realization = find_in_sequence(lambda r: r.get_label() == label, realizations)
        if realization:
            realization.guid = guid
            realization.save()
            for publication in realization.publications.all():
                publication.name = guid
                try:
                    publication_content = et.fromstring(publication.content.encode("utf-8"))
                    if publication.format == QPublicationFormats.CIM_XML:
                        # old style of publications uses namespaces...
                        namespaces = publication_content.nsmap
                        namespaces["cim"] = namespaces.pop(None)
                        publication_content_id = get_index(publication_content.xpath("//cim:documentID", namespaces=namespaces), 0)
                    else:
                        # new style of publications is better...
                        publication_content_id = get_index(publication_content.xpath("//id"), 0)
                    if publication_content_id is not None:
                        publication_content_id.text = guid
                        publication.content = et.tostring(publication_content)
                except XMLSyntaxError:
                    print("There is a problem w/ a publication version '{0}' for the '{1}' realization in project '{2}'".format(publication.version, label, project_name))
                    pass
                publication.save()
        else:
            print("Could not find a realization w/ label '{0}' in project '{1}'; skipping".format(label, project_name))
