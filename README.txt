####################
# Django-CIM-Forms #
####################

Django-CIM-Forms (DCF) is a set of Django Applications that generate webforms based on CIM-compatible metadata models and controlled vocabularies for use in a Django Framework.

DCF is separated into a top-level application ("django_cim_forms") which contains all of the base classes and generic code used to work with models and forms, and sub-applications for particular versions of the CIM (currently, only "cim_1_5" exists) which contain all of the models and base forms for the classes defined in that version of the CIM.  

Additionally, to fully use DCF, one or more custom applications are required.  These define a subset of CIM models and forms that should be rendered for a particular user community.  DCF provides a set of functions (which in the long-term will be made accessible via an Admin GUI) to customize how those models and forms are rendered.  Without these customizations, the base models and forms may be unsuitable for users.  Advice on how to customize models and forms is given at the bottom of this document.

################
# Requirements #
################

1.  As a Django Application, DCF must be integrated into an existing Django Project.
2.  That project must be deployed in an environment with the following packages:
2a. Python 2.6+
2b. Django 1.4+
2c. lxml 2.3.3+ (used for parsing and manipulating XML files)
2d. distribute  (used as part of the installation process)
2e. pip (used as part of the installation process)
3.  DCF makes heavy use of JQuery, but all of the required libraries are included as part of the distribution
4.  Using a virtual Python environment is recommended, but not required.


