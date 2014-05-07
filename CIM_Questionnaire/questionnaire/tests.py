
####################
#   CIM_Questionnaire
#   Copyright (c) 2013 CoG. All rights reserved.
#
#   Developed by: Earth System CoG
#   University of Colorado, Boulder
#   http://cires.colorado.edu/
#
#   This project is distributed according to the terms of the MIT license [http://www.opensource.org/licenses/MIT].
####################

__author__="allyn.treshansky"
__date__ ="Dec 9, 2013 4:33:11 PM"

"""
.. module:: tests

Summary of module goes here

"""

import os

from django.test import TestCase
from django.test.client import RequestFactory

from questionnaire.models import *
from questionnaire.views import *

from questionnaire.models.metadata_version import UPLOAD_PATH as VERSION_UPLOAD_PATH
from questionnaire.models.metadata_categorization import UPLOAD_PATH as CATEGORIZATION_UPLOAD_PATH
from questionnaire.models.metadata_vocabulary import UPLOAD_PATH as VOCABULARY_UPLOAD_PATH


class MetadataTest(TestCase):

    def setUp(self):
        # request factory for all tests
        self.factory = RequestFactory()

        # ensure that there is no categorized metadata before a new one is loaded
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),0)

        # create a categorization
        test_categorization_name = "test_categorization.xml"
        test_categorization = MetadataCategorization(name="test",file=os.path.join(CATEGORIZATION_UPLOAD_PATH,test_categorization_name))
        test_categorization.save()
        
        # ensure the categorization is saved to the database
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)

        # create a version
        test_version_name = "test_version.xml"
        test_version = MetadataVersion(name="test",file=os.path.join(VERSION_UPLOAD_PATH,test_version_name))
        test_version.categorization = test_categorization   # associate the "test" categorization w/ the "test" version
        test_version.save()

        # create a vocabulary
        test_vocabulary_name = "test_vocabulary.xml"
        test_vocabulary = MetadataVocabulary(name="test",file=os.path.join(VOCABULARY_UPLOAD_PATH,test_vocabulary_name))
        test_vocabulary.document_type = "modelcomponent"
        test_vocabulary.save()

        # register a version
        self.assertEqual(test_version.registered,False)
        test_version.register()
        self.assertEqual(test_version.registered,True)

        # register a categorization        
        self.assertEqual(test_categorization.registered,False)
        test_categorization.register()
        self.assertEqual(test_categorization.registered,True)

        # register a vocabulary
        self.assertEqual(test_vocabulary.registered,False)
        test_vocabulary.register()
        self.assertEqual(test_vocabulary.registered,True)

        self.version = test_version
        self.categorization = test_categorization
        self.vocabulary = test_vocabulary
        
    def tearDown(self):
        pass
    
    def test_setUp(self):
        qs = MetadataCategorization.objects.all()
        self.assertEqual(len(qs),1)


##class MetadataEditingViewTest(TestCase):
##
### TODO: fixtures not currently working
### (perhaps b/c of the order in which fixtures are loaded)
###    fixtures = ["questionnaire_test_all.json"]
##
##    def setUp(self):
##        super(MetadataEditingViewTest,self).setUp()
##        self.factory = RequestFactory()
##
##    def tearDown(self):
##        pass
##
##    def test_default(self):
##        self.assertTrue(True)
##
##    def test_questionnaire_edit_new_get(self):
##        project_name = "downscaling"
##        version_name = "flarble"
##        model_name = "modelcomponent"
##        request_url = "/%s/edit/%s/%s" % (project_name,version_name,model_name)
##        #import ipdb; ipdb.set_trace()
##        request = self.factory.get(request_url)
##        response = edit_new(request)
##        self.assertEqual(response.status_code,200)


class MetadataVersionTest(MetadataTest):

    def test_register_models(self):

        models = MetadataModelProxy.objects.all()

        excluded_fields = ["id","version"]
        serialized_models = [model_to_dict(model,exclude=excluded_fields) for model in models]

        to_test = [{'order': 0, 'documentation': u'blah', 'name': u'modelcomponent', 'stereotype': u'document', 'package': None}, {'order': 1, 'documentation': u'blah', 'name': u'gridspec', 'stereotype': u'document', 'package': None}]

        # test that the models have the expected standard fields
        for s,t in zip(serialized_models,to_test):            
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for model in models:
            self.assertEqual(model.version,self.version)

    def test_register_standard_properties(self):

        models = MetadataModelProxy.objects.all()

        to_test = [
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
            ],
            [
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'shortName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 0, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u'DEFAULT'},
                {'field_type': u'ENUMERATION', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'type', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'one|two|three', 'documentation': u'', 'order': 1, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'longName', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 2, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'description', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 3, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'purpose', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 4, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'license', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 5, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'ATOMIC', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'timing', 'enumeration_multi': False, 'relationship_target_name': u'', 'enumeration_choices': u'', 'documentation': u'', 'order': 6, 'enumeration_open': False, 'relationship_cardinality': u'', 'atomic_type': u"['TEXT']"},
                {'field_type': u'RELATIONSHIP', 'atomic_default': u'', 'enumeration_nullable': False, 'name': u'grid', 'enumeration_multi': False, 'relationship_target_name': u'gridspec', 'enumeration_choices': u'', 'documentation': u'', 'order': 7, 'enumeration_open': False, 'relationship_cardinality': u'0|*', 'atomic_type': u"['TEXT']"}
            ]
        ]

        excluded_fields = ["id","model_proxy","relationship_target_model"]

        for model,standard_properties_to_test in zip(models,to_test):
            standard_properties = model.standard_properties.all()
            serialized_standard_properties = [model_to_dict(standard_property,exclude=excluded_fields) for standard_property in standard_properties]

            # test that the properties have the expected standard fields
            for serialized_standard_property,standard_property_to_test in zip(serialized_standard_properties,standard_properties_to_test):
                self.assertDictEqual(serialized_standard_property,standard_property_to_test)

            for standard_property in standard_properties:
                self.assertEqual(standard_property.model_proxy,model)

                if standard_property.relationship_target_model or standard_property.relationship_target_name:
                    self.assertEqual(standard_property.relationship_target_model.name,standard_property.relationship_target_name)


class MetadataCategorizationTest(MetadataTest):

    def test_register_standard_categories(self):

        categories = MetadataStandardCategoryProxy.objects.all()

        excluded_fields = ["id","categorization","properties"]
        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]

        categories_to_test = [
            {'name': u'Document Properties', 'key': u'document-properties', 'order': 1, 'description': u''},
            {'name': u'Basic Properties', 'key': u'basic-properties', 'order': 2, 'description': u''},
            {'name': u'Component Description', 'key': u'component-description', 'order': 3, 'description': u''},
        ]


        # test that the categories have the expected standard fields
        for s,t in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(s,t)
 
        # test that they have the expected foreignkeys
        for category in categories:
            self.assertEqual(category.categorization,self.categorization)
            # TODO: TEST THAT "PROPETIES" M2M FIELD IS AS EXPECTED

class MetadataVocabularyTest(MetadataTest):

    def test_register_components(self):
        components = MetadataComponentProxy.objects.all()

        excluded_fields = ["vocabulary","parent","id"]
        serialized_components = [model_to_dict(component,exclude=excluded_fields) for component in components]

        components_to_test = [
            {'order': 1, 'documentation': u'Definition of component type Atmosphere required', 'name': u'atmosphere'},
            {'order': 2, 'documentation': u'Definition of component type AtmosKeyProperties required', 'name': u'atmoskeyproperties'},
            {'order': 3, 'documentation': u'Definition of component type TopOfAtmosInsolation required', 'name': u'topofatmosinsolation'},
            {'order': 4, 'documentation': u'Definition of component type AtmosSpaceConfiguration required', 'name': u'atmosspaceconfiguration'},
            {'order': 5, 'documentation': u'Definition of component type AtmosHorizontalDomain required', 'name': u'atmoshorizontaldomain'},
            {'order': 6, 'documentation': u'Definition of component type AtmosDynamicalCore required', 'name': u'atmosdynamicalcore'},
            {'order': 7, 'documentation': u'Definition of component type AtmosAdvection required', 'name': u'atmosadvection'}, 
            {'order': 8, 'documentation': u'Definition of component type AtmosRadiation required', 'name': u'atmosradiation'}, 
            {'order': 9, 'documentation': u'Definition of component type AtmosConvectTurbulCloud required', 'name': u'atmosconvectturbulcloud'},
            {'order': 10, 'documentation': u'Definition of component type AtmosCloudScheme required', 'name': u'atmoscloudscheme'},
            {'order': 11, 'documentation': u'Definition of component type CloudSimulator required', 'name': u'cloudsimulator'},
            {'order': 12, 'documentation': u'Definition of component type AtmosOrographyAndWaves required', 'name': u'atmosorographyandwaves'}
        ]
        
        # test that the components have the expected standard fields
        for s,t in zip(serialized_components,components_to_test):
            self.assertDictEqual(s,t)

        # test that they have the expected foreignkeys
        for component in components:
            self.assertEqual(component.vocabulary,self.vocabulary)
            # TODO: TEST THAT "PARENT" FK FIELD IS AS EXPECTED

    def test_register_scientific_properties(self):
        properties = MetadataScientificPropertyProxy.objects.all().order_by("component__order","category__order","order")

        excluded_fields = ["id","category","component"]
        serialized_properties = [model_to_dict(property,exclude=excluded_fields) for property in properties]
        
        properties_to_test = [
            {'field_type': None, 'name': u'ModelFamily', 'documentation': u'Type of atmospheric model.', 'choice': u'XOR', 'values': u'AGCM|ARCM|other|N/A', 'order': 0}, {'field_type': None, 'name': u'BasicApproximations', 'documentation': u'Basic fluid dynamics approximations made in the atmospheric model.', 'choice': u'OR', 'values': u'primitive equations|non-hydrostatic|anelastic|Boussinesq|hydrostatic|quasi-hydrostatic|other|N/A', 'order': 1}, {'field_type': None, 'name': u'VolcanoesImplementation', 'documentation': u'How the volcanoes effect is modeled in the atmophere.', 'choice': u'XOR', 'values': u'none|via high frequency solar contant anomaly|via stratospheric aerosols optical thickness|other|N/A', 'order': 2}, {'field_type': None, 'name': u'ImpactOnOzone', 'documentation': u'Impact of TOA radiation on stratospheric ozone.', 'choice': u'XOR', 'values': u'yes|no', 'order': 0}, {'field_type': None, 'name': u'Type', 'documentation': u'Time adaptation of the solar constant.', 'choice': u'XOR', 'values': u'fixed|transient|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Type', 'documentation': u'Time adaptation of the orbital parameters.', 'choice': u'XOR', 'values': u'fixed|transient|other|N/A', 'order': 0}, {'field_type': None, 'name': u'ComputationMethod', 'documentation': u'Method for computing orbital parameters.', 'choice': u'XOR', 'values': u'Berger 1978|Laskar 2004|other|N/A', 'order': 1}, {'field_type': None, 'name': u'OrographyType', 'documentation': u'Time adaptation of the orography.', 'choice': u'XOR', 'values': u'present-day|modified|other|N/A', 'order': 0}, {'field_type': None, 'name': u'VerticalCoordinateSystem', 'documentation': u'vertical coordinate system.', 'choice': u'XOR', 'values': u'fixed pressure surfaces|pressure height|geometric height|hybrid sigma-pressure layers|hybrid floating Lagrangian|isentropic|sigma|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopModelLevel', 'documentation': u'Level at top of the atmosphere.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'NumberOfLevels', 'documentation': u'Total number of vertical levels.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'NumberOfLevelsBellow850hPa', 'documentation': u'Number of vertical levels bellow 850 hPa.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'NumberOfLevelsAbove200hPa', 'documentation': u'Number of vertical levels above 200 hPa.', 'choice': u'keyboard', 'values': u'', 'order': 4}, {'field_type': None, 'name': u'GridType', 'documentation': u'Geometry type of the horizontal grid.', 'choice': u'XOR', 'values': u'latitude-longitude retangular|latitude-longitude|reduced gaussian|other|N/A', 'order': 0}, {'field_type': None, 'name': u'PoleSingularityTreatment', 'documentation': u'Method used to deal with the pole singularities.', 'choice': u'XOR', 'values': u'filter|pole rotation|artificial island|none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'MeanZonalResolution', 'documentation': u'Mean zonal resolution.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'MeanMeridionalResolution', 'documentation': u'Mean meridional resolution.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'EquatorMeridionalRefinement', 'documentation': u'Resolution at equator.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'SpecialRefinement', 'documentation': u'Description of any other special gid refinement (location, resolution).', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'LatMin', 'documentation': u'Southern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'LatMax', 'documentation': u'Northern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'LonMin', 'documentation': u'Western boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'LonMax', 'documentation': u'Eastern boundary of the geographical domain.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'ListOfPrognosticVariables', 'documentation': u'List of the prognostic variables of the model.', 'choice': u'OR', 'values': u'surface pressure|wind components|divergence/curl|temperature|potential temperature|total water|vapour/solid/liquid|total water moments|clouds|radiation|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopBoundaryCondition', 'documentation': u'Type of boundary layer at top of the model.', 'choice': u'XOR', 'values': u'sponge layer|radiation boundary condition|other|N/A', 'order': 1}, {'field_type': None, 'name': u'HeatTreatmentAtTop', 'documentation': u'Description of any specific treatment of heat at top of the model.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'WindTreatmentAtTop', 'documentation': u'Description of any specific treatment of wind at top of the model.', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'LateralBoundaryCondition', 'documentation': u'Type of lateral boundary condition (only if the model is a RCM).', 'choice': u'XOR', 'values': u'sponge layer|radiation boundary condition|none|other|N/A', 'order': 4}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of time stepping scheme.', 'choice': u'XOR', 'values': u'Adam Bashford|Explicit|Implicit|Semi-Implicit|LeapFrog|Multi-step|Runge Kutta fifth order|Runge Kutta second order|Runge Kutta third order|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TimeStep', 'documentation': u'Time step of the model.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of horizontal discretization scheme.', 'choice': u'XOR', 'values': u'spectral|fixed grid|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'commonly used name of the horizontal diffusion scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeMethod', 'documentation': u'Numerical method used by horizontal diffusion scheme.', 'choice': u'XOR', 'values': u'iterated Laplacian|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for tracers advection scheme.', 'choice': u'XOR', 'values': u'Prather|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of numerical scheme used for advection of tracers.', 'choice': u'XOR', 'values': u'Eulerian|Lagrangian|semi-Lagrangian|mass-conserving|mass-conserving / finite volume (Lin-Rood)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'ConservedQuantities', 'documentation': u'Quantities conserved trought tracers advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'ConservationMethod', 'documentation': u'Method used to ensure conservation in tracers advection scheme.', 'choice': u'OR', 'values': u'conservation fixer|other|N/A', 'order': 3}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for momentum advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of numerical scheme used for advection of momentum.', 'choice': u'XOR', 'values': u'Eulerian|Lagrangian|Semi-Lagrangian|Mass-conserving|Mass-conserving / Finite volume (Lin-Rood)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'ConservedQuantities', 'documentation': u'Quantities conserved trought momentum advection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'ConservationMethod', 'documentation': u'Method used to ensure conservation in momentum advection scheme.', 'choice': u'OR', 'values': u'conservation fixer|other|N/A', 'order': 3}, {'field_type': None, 'name': u'TimeStep', 'documentation': u'Time step of the radiative scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'AerosolTypes', 'documentation': u'Types of aerosols whose radiative effect is taken into account in the atmospheric model.', 'choice': u'OR', 'values': u'sulphate|nitrate|sea salt|dust|ice|organic|BC (black carbon / soot)|SOA (secondary organic aerosols)|POM (particulate organic matter)|polar stratospheric ice|NAT (nitric acid trihydrate)|NAD (nitric acid dihydrate)|STS (supercooled ternary solution aerosol particule)|other|N/A', 'order': 1}, {'field_type': None, 'name': u'GHG-Types', 'documentation': u'GHG whose radiative effect is taken into account in the atmospheric model.', 'choice': u'OR', 'values': u'CO2|CH4|N2O|CFC|H2O|O3|other|N/A', 'order': 2}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for longwave radiation parametrisation.', 'choice': u'XOR', 'values': u'Wide-band model|Wide-band (Morcrette)|K-correlated|K-correlated (RRTM)|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeMethod', 'documentation': u'Method for the radiative transfert calculations used in the longwave scheme.', 'choice': u'XOR', 'values': u'Two-stream|Layer interaction|other|N/A', 'order': 1}, {'field_type': None, 'name': u'NumberOfSpectralIntervals', 'documentation': u'Number of spectral interval of the longwave radiation scheme.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for shortwave radiation parametrization.', 'choice': u'XOR', 'values': u'Wide-band model|Wide-band model (Fouquart)|other|N/A', 'order': 0}, {'field_type': None, 'name': u'NumberOfSpectralIntervals', 'documentation': u'Number of spectral intervals of the short radiation scheme.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'ice', 'documentation': u'Radiative properties of ice cristals in clouds.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'liquid', 'documentation': u'Radiative properties of cloud droplets.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for boundary layer tubulence scheme.', 'choice': u'XOR', 'values': u'Mellor-Yamada|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of turbulence in the boundary layer.', 'choice': u'XOR', 'values': u'TKE prognostic|TKE diagnostic|TKE coupled with water|Vertical profile of Kz|other|N/A', 'order': 1}, {'field_type': None, 'name': u'CounterGradient', 'documentation': u'Application of a counter-gradient term for calculation of the vertical turbulent heat fluxes in case of slighlty stable layer.', 'choice': u'XOR', 'values': u'yes|no', 'order': 2}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for deep convection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of deep convection.', 'choice': u'XOR', 'values': u'Mass-flux|Adjustment|other|N/A', 'order': 1}, {'field_type': None, 'name': u'Processes', 'documentation': u'Physical processes taken into account in the parametrization of the deep convection.', 'choice': u'OR', 'values': u'vertical momentum transport|convective momentum transport (CMT)|penetrative convection effects included|representation of updrafts and downdrafts|radiative effects of anvils|entrainment|detrainment|other|N/A', 'order': 2}, {'field_type': None, 'name': u'Method', 'documentation': u'Method used for parametrization of shallow convection.', 'choice': u'XOR', 'values': u'same as deep (unified)|included in Boundary Layer Turbulence|separated|other|N/A', 'order': 0}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name for mid-level convection scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'SchemeType', 'documentation': u'Type of scheme used for parametrization of mid-level convection.', 'choice': u'XOR', 'values': u'mass-flux|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name of the large scale precipitation parametrization scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'PrecipitatingHydrometeors', 'documentation': u'Precipitating hydrometeors in the large scale precipitation scheme.', 'choice': u'OR', 'values': u'liquid rain|snow|hail|graupel|cats & dogs|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SchemeName', 'documentation': u'Commonly used name of the microphysics parametrization scheme.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'Processes', 'documentation': u'Description of the microphysics processes that are taken into account in the microphysics scheme.', 'choice': u'OR', 'values': u'mixed phase|cloud droplets|cloud ice|ice nucleation|water vapour deposition|effect of raindrops|effect of snow|effect of graupel|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SeparatedCloudTreatment', 'documentation': u'Different cloud schemes for the different types of clouds (convective, stratiform and bondary layer clouds).', 'choice': u'XOR', 'values': u'yes|no', 'order': 0}, {'field_type': None, 'name': u'CloudOverlap', 'documentation': u'Method for taking into account overlapping of cloud layers.', 'choice': u'XOR', 'values': u'random|none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'Processes', 'documentation': u'Cloud processes included in the cloud scheme (e.g. entrainment, detrainment, bulk cloud, etc.).', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'Type', 'documentation': u'Approach used for cloud water content and fractional cloud cover.', 'choice': u'XOR', 'values': u'prognostic|diagnostic|other|N/A', 'order': 0}, {'field_type': None, 'name': u'FunctionName', 'documentation': u'Commonly used name of the probability density function (PDF) representing distribution of water vapor within a grid box.', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'FunctionOrder', 'documentation': u'Order of the function (PDF) used to represent subgrid scale water vapor distribution.', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'CouplingWithConvection', 'documentation': u'Cloud formation coupled with convection. ', 'choice': u'XOR', 'values': u'coupled with deep|coupled with shallow|coupled with deep and shallow|not coupled with convection|other|N/A', 'order': 3}, {'field_type': None, 'name': u'COSPRunConfiguration', 'documentation': u'Method used to run the CFMIP Observational Simulator Package.', 'choice': u'XOR', 'values': u'inline|offline|none|other|N/A', 'order': 0}, {'field_type': None, 'name': u'NumberOfGridpoints', 'documentation': u'Number of gridpoints used. ', 'choice': u'keyboard', 'values': u'', 'order': 1}, {'field_type': None, 'name': u'NumberOfColumns', 'documentation': u'Number of subcolumns used. ', 'choice': u'keyboard', 'values': u'', 'order': 2}, {'field_type': None, 'name': u'NumberOfLevels', 'documentation': u'Number of model levels used. ', 'choice': u'keyboard', 'values': u'', 'order': 3}, {'field_type': None, 'name': u'RadarFrequency', 'documentation': u'CloudSat radar frequency.', 'choice': u'keyboard', 'values': u'', 'order': 0}, {'field_type': None, 'name': u'RadarType', 'documentation': u'Type of radar - surface or spaceborne?', 'choice': u'XOR', 'values': u'surface|spaceborne|other|N/A', 'order': 1}, {'field_type': None, 'name': u'UseGasAbsorption', 'documentation': u'Include gaseous absorption?', 'choice': u'XOR', 'values': u'yes|no', 'order': 2}, {'field_type': None, 'name': u'UseEffectiveRadius', 'documentation': u'Is effective radius used by the radar simulator?', 'choice': u'XOR', 'values': u'yes|no', 'order': 3}, {'field_type': None, 'name': u'LidarIceType', 'documentation': u'Ice particle shape in lidar calculations.', 'choice': u'XOR', 'values': u'Ice spheres|Ice non-spherical|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Overlap', 'documentation': u'Overlap type.', 'choice': u'XOR', 'values': u'max|random|max / random|other|N/A', 'order': 1}, {'field_type': None, 'name': u'TopHeight', 'documentation': u'Cloud top height management. e.g. adjusted using both a computed infrared brightness temperature and visible optical depth to adjust cloud top pressure. ', 'choice': u'XOR', 'values': u'no adjustment|IR brightness|IR brightness and visible optical depth|other|N/A', 'order': 0}, {'field_type': None, 'name': u'TopHeightDirection', 'documentation': u'\nDirection for finding the radiance determined cloud-top pressure.  \nAtmosphere pressure level with interpolated temperature equal to the radiance determined cloud-top pressure.', 'choice': u'XOR', 'values': u'lowest altitude level|highest altitude level|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SpongeLayer', 'documentation': u'Sponge layer in the upper layers in order to avoid gravitywaves reflection at top.', 'choice': u'XOR', 'values': u'none|other|N/A', 'order': 0}, {'field_type': None, 'name': u'Background', 'documentation': u'Background distribution of waves (???).', 'choice': u'XOR', 'values': u'none|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SubGridScaleOrography', 'documentation': u'Subgrid scale orography effects taken into account.', 'choice': u'OR', 'values': u'effect on drag|effect on lifting|other|N/A', 'order': 2}, {'field_type': None, 'name': u'SourceMechanisms', 'documentation': u'Physical mechanisms generating orographic gravity waves.', 'choice': u'OR', 'values': u'linear mountain waves|hydraulic jump|envelope orography|statistical sub-grid scale variance|other|N/A', 'order': 0}, {'field_type': None, 'name': u'CalculationMethod', 'documentation': u'Calculation method for orographic gravity waves.', 'choice': u'OR', 'values': u'non-linear calculation|more than two cardinal directions|other|N/A', 'order': 1}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for orographic gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 2}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for orographic gravity waves.', 'choice': u'XOR', 'values': u'total wave|single wave|spectral|linear|other|N/A', 'order': 3}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for convective gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 0}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for convective gravity waves.', 'choice': u'XOR', 'values': u'total Wave|single wave|spectral|linear|other|N/A', 'order': 1}, {'field_type': None, 'name': u'SourceMechanisms', 'documentation': u'Physical mechanisms generating non-orographic gravity waves.', 'choice': u'OR', 'values': u'convection|precipitation|background spectrum|other|N/A', 'order': 0}, {'field_type': None, 'name': u'CalculationMethod', 'documentation': u'Calculation method for non-orographic gravity waves.', 'choice': u'OR', 'values': u'spatially dependent|temporally dependent|other|N/A', 'order': 1}, {'field_type': None, 'name': u'PropagationScheme', 'documentation': u'Type of propagation scheme for non-orographic gravity waves.', 'choice': u'XOR', 'values': u'linear theory|non-linear theory|other|N/A', 'order': 2}, {'field_type': None, 'name': u'DissipationScheme', 'documentation': u'Type of dissipation scheme for non-orographic gravity waves.', 'choice': u'XOR', 'values': u'total wave|single wave|spectral|linear|other|N/A', 'order': 3}
        ]
        
        # test that the components have the expected standard fields
        for s,t in zip(serialized_properties,properties_to_test):
            self.assertDictEqual(s,t)

        # TODO: TEST THAT "category" & "component" FIELDS ARE AS EXPECTED

    def test_register_scientific_categories(self):

        categories = MetadataScientificCategoryProxy.objects.all()

        excluded_fields = ["id","vocabulary","properties","component"]
        serialized_categories = [model_to_dict(category,exclude=excluded_fields) for category in categories]

        categories_to_test = [
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'general-attributes', 'description': None, 'name': u'General Attributes', 'order': 0},
            {'key': u'orographicgravitywaves', 'description': None, 'name': u'OrographicGravityWaves', 'order': 1},
            {'key': u'boundarylayerturbulence', 'description': None, 'name': u'BoundaryLayerTurbulence', 'order': 1},
            {'key': u'orography', 'description': None, 'name': u'Orography', 'order': 1},
            {'key': u'cloudschemeattributes', 'description': None, 'name': u'CloudSchemeAttributes', 'order': 1},
            {'key': u'grid', 'description': None, 'name': u'Grid', 'order': 1},
            {'key': u'solarconstant', 'description': None, 'name': u'SolarConstant', 'order': 1},
            {'key': u'cospattributes', 'description': None, 'name': u'COSPAttributes', 'order': 1},
            {'key': u'timesteppingframework', 'description': None, 'name': u'TimeSteppingFramework', 'order': 1},
            {'key': u'tracers', 'description': None, 'name': u'Tracers', 'order': 1},
            {'key': u'longwave', 'description': None, 'name': u'Longwave', 'order': 1},
            {'key': u'shortwave', 'description': None, 'name': u'Shortwave', 'order': 2},
            {'key': u'orbitalparameters', 'description': None, 'name': u'OrbitalParameters', 'order': 2},
            {'key': u'verticaldomain', 'description': None, 'name': u'VerticalDomain', 'order': 2},
            {'key': u'resolution', 'description': None, 'name': u'Resolution', 'order': 2},
            {'key': u'horizontaldiscretization', 'description': None, 'name': u'HorizontalDiscretization', 'order': 2},
            {'key': u'momentum', 'description': None, 'name': u'Momentum', 'order': 2},
            {'key': u'deepconvection', 'description': None, 'name': u'DeepConvection', 'order': 2},
            {'key': u'subgridscalewaterdistribution', 'description': None, 'name': u'SubGridScaleWaterDistribution', 'order': 2},
            {'key': u'inputsradar', 'description': None, 'name': u'InputsRadar', 'order': 2},
            {'key': u'convectivegravitywaves', 'description': None, 'name': u'ConvectiveGravityWaves', 'order': 2},
            {'key': u'horizontaldiffusion', 'description': None, 'name': u'HorizontalDiffusion', 'order': 3},
            {'key': u'extent', 'description': None, 'name': u'Extent', 'order': 3},
            {'key': u'cloudradiativeproperties', 'description': None, 'name': u'CloudRadiativeProperties', 'order': 3},
            {'key': u'non-orographicgravitywaves', 'description': None, 'name': u'Non-OrographicGravityWaves', 'order': 3},
            {'key': u'inputslidar', 'description': None, 'name': u'InputsLidar', 'order': 3},
            {'key': u'shallowconvection', 'description': None, 'name': u'ShallowConvection', 'order': 3},
            {'key': u'otherconvection', 'description': None, 'name': u'OtherConvection', 'order': 4},
            {'key': u'isscpattributes', 'description': None, 'name': u'ISSCPAttributes', 'order': 4},
            {'key': u'largescaleprecipitation', 'description': None, 'name': u'LargeScalePrecipitation', 'order': 5},
            {'key': u'microphysics', 'description': None, 'name': u'Microphysics', 'order': 6}
        ]


        # test that the categories have the expected standard fields
        for s,t in zip(serialized_categories,categories_to_test):
            self.assertDictEqual(s,t)
