Overview of DCF
===============

Top-Level classes
-----------------

There are four high-level classes that must be properly loaded into Django-CIM-Forms (DCF) to be able to edit CIM Docuemnts and/or customize CIM Document Forms.  Each of these classes should be governed by a separate (though potentially overlapping) group.


MetadataVersion
~~~~~~~~~~~~~~~

CIM Versions are obviously governed by the group that oversees the content of the CIM Metadata Standard.  DCF requires a CIM version to be "registered" with the application in order to work.  The CIM is defined at the conceptual level as a UML Model (the "CONCIM").  The CONCIM can be translated into different application schemas.  Currently, translating from UML to XSD is an automated process while translating from UML to Django Classes is a manual process.  In the long-term this will be automated.

MetadataCategorization
~~~~~~~~~~~~~~~~~~~~~~

ES-DOC developers are in charge of the main look-and-feel of the metadata entry forms.  This includes the set of standard tabs (or "attribute categories") that are rendered across the tops of the forms.  That information is not part of the CIM Schemas, nor is it part of any CV.

MetadataVocabulary
~~~~~~~~~~~~~~~~~~

A MetadataVocabulary represents a CIM Controlled Vocabulary (CV).  The CIM schemas (which are stored as MetadataVersions above) only define the structure of metadata documents.  CVs define the terms, and relationships among terms, that can be used within that structure.  There will exist different CVs for different user communities.  A CV is stored as an XML file.  Within DCF, that file must be registered to be used.

MetadataProject
~~~~~~~~~~~~~~~

It is assumed that DCF will be integrated into the workflow of climate projects.  Administrators of those projects are responsible for the customization of metadata entry forms.  They use the provided DCF customization GUI to define how each CIM Document for their project ought to be rendered in the editing form (ie: which CIM attributes should appear and where, what documentation to include, etc.).

Using the CIM Editor
--------------------

Once all of these classes have been setup by the appropriate groups, the final group, the End Users, can utilize the customized forms to create and modify CIM documents.  When those documents are complete, they can be published to DCF's ATOM feed.

