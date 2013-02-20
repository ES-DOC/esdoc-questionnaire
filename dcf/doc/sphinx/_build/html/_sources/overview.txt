Overview of DCF
===============

Top-Level classes
-----------------

There are four high-level classes that must be properly loaded into Django-CIM-Forms (DCF) to be able to edit CIM Docuemnts and/or customize CIM Document Forms.


MetadataVersion
~~~~~~~~~~~~~~~

asdf

MetadataCategorization
~~~~~~~~~~~~~~~~~~~~~~

asdf

MetadataVocabulary
~~~~~~~~~~~~~~~~~~

asdf

MetadataProject
~~~~~~~~~~~~~~~

asdf

Obviously this is the group that oversees the content of the CIM Metadata Standard.  DCF requires a CIM version to be "registered" with the application in order to work.  The CIM is defined at the conceptual level as a UML Model (the "CONCIM").  The CONCIM can be translated into different application schemas.  Currently, translating from UML to XSD is an automated process while translating from UML to Django Classes is a manual process.  In the long-term this will be automated.

Controlled Vocabulary (CV) Governance Community
-----------------------------------------------

The CIM schemas only define the structure of metadata documents.  Controlled Vocabularies (CVs) define the terms, and relationships among terms, that can be used within that structure.  There will exist different CVs for different user communities.  A CV is stored as an XML file.  Within DCF, that file must be registered to be used.

ES-DOC Community
----------------

ES-DOC developers are in charge of the main look-and-feel of the metadata entry forms.  This includes the set of standard tabs (or "attribute categories") that are rendered across the tops of the forms.  That information is not part of the CIM Schemas, nor is it part of any CV.

DCF / ES-DOC / DCF Project Administrators
-----------------------------------------



DCF Project Administrators
--------------------------

This group is responsible for the customization of metadata entry forms.  They use the provided DCF customization GUI to define how each CIM Document for their project ought to be rendered in the editing form (ie: which CIM attributes should appear and where, what documentation to include, etc.).

DCF End Users
-------------

This group is self-explanatory.  They will be using the customized forms to create and modify CIM documents.  When those documents are complete, they can be published to DCF's ATOM feed.

