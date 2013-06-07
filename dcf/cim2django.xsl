<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="2.0" 
    xmlns:UML="omg.org/UML1.3"
    exclude-result-prefixes="UML">
       
    <!-- ************ -->
    <!-- header stuff -->
    <!-- ************ -->
    
    <!-- don't output XML or HTML -->
    <xsl:output method="text"/>
    
    <!-- ignore free text and whitespace-->
    <xsl:template match="text()"/>
    <xsl:strip-space elements="*"/>

    <!-- some useful global variables  -->   
    <xsl:param name="application-name">dcf</xsl:param>
    <xsl:param name="module-name">undefined</xsl:param>
    <xsl:param name="metadata-name">CIM</xsl:param>
    <xsl:param name="version">undefined</xsl:param>
    <xsl:param name="sort-elements">false</xsl:param>
    <xsl:param name="debug">false</xsl:param>    
    
    <xsl:variable name="lowerCase">abcdefghijklmnopqrstuvwxyz</xsl:variable>
    <xsl:variable name="upperCase">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>
    <xsl:variable name="tab"><xsl:text>    </xsl:text></xsl:variable>
    <xsl:variable name="newline"><xsl:text>       
</xsl:text>
    </xsl:variable>
    
        
    <!-- ********************* -->
    <!-- "top-level" templates -->
    <!-- ********************* -->
    
    <!-- EA outputs XMI v1.1; so this XSL is tailored to that -->
    <!-- strange things might happen at other versions -->
    <xsl:template match="XMI[@xmi.version='1.1']">
        <xsl:if test="$version='undefined'">
            <xsl:message terminate="yes">
                <xsl:text> please specify a version parameter </xsl:text>
            </xsl:message>
        </xsl:if>
        <xsl:if test="$module-name='undefined'">
            <xsl:message terminate="yes">
                <xsl:text> please supply the name of the module to be generated </xsl:text>
            </xsl:message>
        </xsl:if>
        <xsl:if test="$debug='true'">
            <xsl:message>
                <xsl:value-of select="$newline"/>
            </xsl:message>
            <xsl:choose>
                <xsl:when test="$sort-elements='true'">
                    <xsl:message>
                        <xsl:text> UML elementws will be processed in lexical order </xsl:text>
                        <xsl:value-of select="$sort-elements"/>
                    </xsl:message>
                </xsl:when>
                <xsl:when test="not($sort-elements='true')">
                    <xsl:message>
                        <xsl:text> UML elements will be processed in the order in which they appear </xsl:text>
                        <xsl:value-of select="$sort-elements"/>
                    </xsl:message>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:message terminate="yes">
                        <xsl:text> invalid sorting order specified </xsl:text>
                    </xsl:message>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        
        <!-- apply templates to the UML:Model -->
        <!-- and ignore  UML:Diagram, etc. -->
        <xsl:apply-templates select="XMI.content/UML:Model"/>
    </xsl:template>
    
    <!-- uh-oh, XMI at a different version -->
    <xsl:template match="XMI">
        <xsl:message terminate="yes">
            <xsl:text>unsupported XMI version: </xsl:text>
            <xsl:value-of select="@xmi.version"/>
        </xsl:message>
    </xsl:template>
    
    
    <!-- every package is its own schema file -->
    <!-- each package includes all other schemas -->
    <xsl:template match="UML:Package">
        <xsl:variable name="packageName" select="@name"/>
    
        <xsl:if test="$debug='true'">
            <xsl:message>
                <xsl:value-of select="$newline"/>
            </xsl:message>
            <xsl:message>
                <xsl:text>processing package: </xsl:text>
                <xsl:value-of select="$packageName"/>
            </xsl:message>
        </xsl:if>

            <!-- if this is the top-level package (ie: the root of the domain model) -->
            <xsl:variable name="depth" select="count(ancestor::UML:Package)"/>
            <xsl:if test="$depth=0">
                
                <xsl:call-template name="CommentTemplate">
                    <xsl:with-param name="string">
                        <xsl:value-of
                            select="concat('auto-generated: ',format-dateTime(current-dateTime(), '[D] [MNn] [Y], [H]:[m]'),' ')"
                        />
                    </xsl:with-param>
                </xsl:call-template>
                
                <xsl:call-template name="CommentTemplate">
                    <xsl:with-param name="string">
                        <xsl:text> module: </xsl:text>
                        <xsl:value-of select="$module-name"/>
                        <xsl:text>.models</xsl:text>
                    </xsl:with-param>
                </xsl:call-template>
                                
from django.db import models        
from <xsl:value-of select="$application-name"/>.models import *
                
#########################################
# this registers this version w/ the db #
#########################################
                
MetadataVersion.factory({
    "name"      :   "<xsl:call-template name="UpperCaseTemplate"><xsl:with-param name="string" select="$metadata-name"/></xsl:call-template>",
    "version"   :   "<xsl:value-of select="$version"/>",
})
                
####################################
# and here are the actual classes  #
####################################
                
                                
            </xsl:if>
            
            <xsl:choose>
                
                <xsl:when test="$packageName='shared'">
                    <xsl:call-template name="CommentTemplate">
                        <xsl:with-param name="string">
                            TODO: DO I WANT TO DO ANYTHING SPECIAL W/ THE "SHARED" PACKAGE?
                        </xsl:with-param>
                    </xsl:call-template> 
                    <xsl:apply-templates/>
                </xsl:when>
                
                <xsl:when test="$packageName='grids'">
                    <xsl:call-template name="CommentTemplate">
                        <xsl:with-param name="string">
                            DELIBERATELY SKIPPING THE "GRIDS" PACKAGE B/C IT HAS TOO MANY EXTERNAL DEPENDENCIES
                        </xsl:with-param>
                    </xsl:call-template>                    
                </xsl:when>
                
                <xsl:otherwise>                
                    <xsl:apply-templates/>                    
                </xsl:otherwise>
                
            </xsl:choose>
                    
    </xsl:template>    
    
    <!-- every UML class (within a package) is either a complexType or a simpleType -->
    <xsl:template match="UML:Package//UML:Class">
        
        <xsl:if test="$debug='true'">
            <xsl:message>
                <xsl:text>processing class: </xsl:text>
                <xsl:value-of select="@name"/>
            </xsl:message>
        </xsl:if>
        
        <xsl:variable name="classStereotype">
            <xsl:call-template name="LowerCaseTemplate">
                <xsl:with-param name="string"
                    select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='stereotype']/@value"
                />
            </xsl:call-template>
        </xsl:variable>        
        
        <xsl:if test="$classStereotype='document'">
            <xsl:if test="$debug='true'">
                <xsl:message>
                    <xsl:text> it's a document </xsl:text>
                </xsl:message>
            </xsl:if>
            <xsl:call-template name="DocumentTemplate"/>
        </xsl:if>
        
        <xsl:choose>
            <xsl:when test="$classStereotype='unused'">
                <xsl:call-template name="UnusedTemplate"/>                    
            </xsl:when>
            
            <xsl:when test="$classStereotype='enumeration'">
                <xsl:if test="$debug='true'">
                    <xsl:message>
                        <xsl:text>it's an enumeration </xsl:text>
                    </xsl:message>
                </xsl:if>                
                <xsl:call-template name="EnumerationTemplate"/>
            </xsl:when>
            
            <xsl:when test="$classStereotype='codelist'">
                <xsl:if test="$debug='true'">
                    <xsl:message>
                        <xsl:text>it's a codelist </xsl:text>
                    </xsl:message>
                </xsl:if>
                <!--<xsl:call-template name="CodeListTemplate"/>-->
                <xsl:call-template name="EnumerationTemplate"/>
            </xsl:when>
            
            <xsl:otherwise>
                <xsl:if test="$debug='true'">
                    <xsl:message>
                        <xsl:text>it's a normal class </xsl:text>
                    </xsl:message>
                </xsl:if>
                <xsl:call-template name="ClassTemplate"/>
            </xsl:otherwise>
            

        </xsl:choose>
        
        
    </xsl:template>

    <!-- *********************************** -->
    <!-- templates for different class types -->
    <!-- *********************************** -->
    
    <!-- Unused Template -->
    <xsl:template name="UnusedTemplate">
        <xsl:variable name="class" select="."/>
        <xsl:call-template name="CommentTemplate">
            <xsl:with-param name="string">
                <xsl:value-of select="$class/@name"/> is not used
            </xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- Document Template -->
    <xsl:template name="DocumentTemplate">
        <xsl:variable name="class" select="."/>
            <xsl:text>
@CIMDocument()</xsl:text>        
    </xsl:template>

    <!-- Enumeration Template -->
    <xsl:template name="EnumerationTemplate">
        <xsl:variable name="class" select="."/>
        <xsl:variable name="class_id" select="@xmi.id"/>
        
        <xsl:variable name="open">
            <xsl:call-template name="CapitalizeTemplate">
                <xsl:with-param name="string">
                    <xsl:value-of select="//UML:TaggedValue[@tag='open'][@modelElement=$class_id]/@value='true'"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="multi">
            <xsl:call-template name="CapitalizeTemplate">
                <xsl:with-param name="string">
                    <!-- TODO: DETERMINE IF ENUMERATION IS MULTI -->
                    <xsl:value-of select="false()"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="nullable">
            <xsl:call-template name="CapitalizeTemplate">
                <xsl:with-param name="string">
                    <!-- TODO: DETERMINE IF ENUMERATION IS NULLABLE -->
                    <xsl:value-of select="false()"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

<xsl:value-of select="$newline"/>
class <xsl:value-of select="@name"/>(MetadataEnumeration):
    class Meta:
        abstract = False
        
    _name        = "<xsl:value-of select="@name"/>"
    _title       = "<xsl:call-template name="SplitStringTemplate"><xsl:with-param name="string"><xsl:value-of select="$class/@name"/></xsl:with-param></xsl:call-template>"
    _description = "<xsl:call-template name="DocumentationTemplate"><xsl:with-param name="string" select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='documentation']/@value"/></xsl:call-template>"
                
    CHOICES = [
    <xsl:for-each select="./UML:Classifier.feature/UML:Attribute[UML:ModelElement.stereotype/UML:Stereotype/@name='enum']">
        <xsl:text>"</xsl:text><xsl:value-of select="@name"/><xsl:text>",</xsl:text><xsl:value-of select="concat($newline,$tab,$tab)"/>
    </xsl:for-each>
    ]
        
    open     = <xsl:value-of select="$open"/>
    nullable = <xsl:value-of select="$nullable"/>
    multi    = <xsl:value-of select="$multi"/>
<xsl:value-of select="$newline"/>        
            
    </xsl:template>
    
    
    <!-- Class Template -->
    <xsl:template name="ClassTemplate">
        <xsl:variable name="class" select="."/>
        <xsl:variable name="class_id" select="@xmi.id"/>
        
        <xsl:variable name="stereotype">
            <xsl:call-template name="LowerCaseTemplate">
                <xsl:with-param name="string"
                    select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='stereotype']/@value"
                />
            </xsl:call-template>
        </xsl:variable>
                        
        <xsl:variable name="internalGeneralisation"
            select="//UML:Generalization[@subtype=$class_id]"/>
        <xsl:variable name="externalGeneralisation"
            select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='genlinks'][1]"/>
        <xsl:variable name="simpleGeneralisation"
            select="starts-with($externalGeneralisation/attribute::value,'Parent=xs:')"/>
        
        <xsl:choose>
            <!-- it might be a specialisation of some other class in the domain model -->
            <xsl:when test="$internalGeneralisation">
                <xsl:variable name="baseClass"
                    select="//UML:Class[@xmi.id=$internalGeneralisation/attribute::supertype]"/>                
class <xsl:value-of select="replace(@name,'-','_')"/>(<xsl:value-of select="$baseClass/@name"/>):                 
            </xsl:when>
            
            <xsl:when test="$externalGeneralisation">
                
                <xsl:if test="not($simpleGeneralisation)">
                    
                    <xsl:variable name="baseClass"
                        select="substring-before(substring-after($externalGeneralisation/attribute::value,'Parent='),';')"/>
class <xsl:value-of select="replace(@name,'-','_')"/>(MetadataModel):
                    <xsl:call-template name="CommentTemplate">
                        <xsl:with-param name="string">
                            <xsl:text>this is acutally an external dependency(</xsl:text>
                            <xsl:value-of select="$baseClass"/>
                            <xsl:text>)</xsl:text>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            
            <xsl:otherwise>
                <xsl:variable name="baseClass">MetadataModel</xsl:variable>
class <xsl:value-of select="replace(@name,'-','_')"/>(<xsl:value-of select="$baseClass"/>):
            </xsl:otherwise>
            
        </xsl:choose>
<!--    
            currently having problems w/ abstract classes
            requires use of generic foreign keys, etc.
    class Meta:
        abstract = <xsl:call-template name="CapitalizeTemplate"><xsl:with-param name="string"><xsl:value-of select="$stereotype='abstract'"></xsl:value-of></xsl:with-param></xsl:call-template>
-->
    class Meta:
        abstract = False
        
    _abstract = <xsl:call-template name="CapitalizeTemplate"><xsl:with-param name="string"><xsl:value-of select="$stereotype='abstract'"></xsl:value-of></xsl:with-param></xsl:call-template>
        
    _name        = "<xsl:value-of select="$class/@name"/>"
    _title       = "<xsl:call-template name="SplitStringTemplate"><xsl:with-param name="string"><xsl:value-of select="$class/@name"/></xsl:with-param></xsl:call-template>"
    _description = "<xsl:call-template name="DocumentationTemplate"><xsl:with-param name="string" select="$class/UML:ModelElement.taggedValue/UML:TaggedValue[@tag='documentation']/@value"/></xsl:call-template>"
        
    def __init__(self,*args,**kwargs):
        super(<xsl:value-of select="$class/@name"/>,self).__init__(*args,**kwargs)
        
    <!-- first look at the UML attributes -->    
    <xsl:for-each select="descendant::UML:Attribute">
                
        <xsl:call-template name="CommentTemplate">
            <xsl:with-param name="string">UML Attribute</xsl:with-param>
        </xsl:call-template> 
        
        <xsl:call-template name="AttributeTemplate">
            <xsl:with-param name="min" select="descendant::UML:TaggedValue[@tag='lowerBound']/@value"/>
            <xsl:with-param name="max" select="descendant::UML:TaggedValue[@tag='upperBound']/@value"/>
            <xsl:with-param name="type" select="descendant::UML:TaggedValue[@tag='type']/@value"/>
            <xsl:with-param name="parent" select="$class"/>
            <xsl:with-param name="stereotype"
                select="translate(descendant::UML:TaggedValue[@tag='stereotype']/@value,$upperCase,$lowerCase)"/>
            <xsl:with-param name="documentation" 
                select="descendant::UML:TaggedValue[@tag='description']/@value"/>
            
        </xsl:call-template>
        
    </xsl:for-each>
        
    <!-- then look if any associations (aggregation/composition) have this class as an endpoint -->
    <xsl:for-each select="//UML:Association[/UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_type' and @value='Aggregation']]"><!--//UML:AssociationEnd[@type=$class/@xmi.id]/ancestor::UML:Association">-->
        
        
        <xsl:variable name="associationTargetEnd" select="./UML:Association.connection/UML:AssociationEnd/UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_end' and @value='target']/ancestor::UML:AssociationEnd"/>       
        <xsl:variable name="associationSourceEnd" select="./UML:Association.connection/UML:AssociationEnd/UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_end' and @value='source']/ancestor::UML:AssociationEnd"/>
        <xsl:variable name="associationRole" select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='lt']/@value"/>
        <xsl:if test="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_targetName' and @value=$class/@name]">
            
            <xsl:variable name="cardinality" select="$associationSourceEnd/@multiplicity"/>
            
            <xsl:call-template name="CommentTemplate">
                <xsl:with-param name="string">UML Association</xsl:with-param>
            </xsl:call-template> 
            
            <xsl:call-template name="AssociationTemplate">
                <xsl:with-param name="min" select="substring-before($cardinality,'..')"/>
                <xsl:with-param name="max" select="substring-after($cardinality,'..')"/>
                <!-- the role name potentially has lots of other junk in it; this gets rid of that junk -->
                <xsl:with-param name="associationName" select=" replace($associationRole,'[^a-zA-Z]','')"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:for-each>
        
    <xsl:value-of select="$newline"/>                
    </xsl:template>

    <xsl:template name="AssociationTemplate">
        <xsl:param name="min">1</xsl:param>
        <xsl:param name="max">1</xsl:param>
        <xsl:param name="type"/>
        <xsl:param name="stereotype"/>
        <xsl:param name="documentation"/>   <!-- no documentation in associations (?) -->
        <xsl:param name="associationName"/>
        
        <xsl:variable name="associationClassName" select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_sourceName']/@value"/>
        <xsl:variable name="associationClass" select="//UML:Class[@name=$associationClassName]"/>
        
        <xsl:value-of select="$tab"/>
        <xsl:choose>
            <xsl:when test="$associationName">
                <xsl:value-of select="$associationName"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="UncapitalizeTemplate">
                    <xsl:with-param name="string" select="$associationClassName"/>                
                </xsl:call-template>                
            </xsl:otherwise>
        </xsl:choose>        
        
        <xsl:text> = </xsl:text>
        <xsl:choose>
            <xsl:when test="$max = '*' or number($max) &gt; 1">
                <xsl:text>MetadataManyToManyField(</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>MetadataManyToOneField(</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        
        <xsl:text>sourceModel='</xsl:text>        
        <xsl:value-of select="concat($module-name,'.')"/>
        <!-- hacky way to get souce model; but it works -->
        <xsl:value-of select="./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_targetName']/@value"/>
        <xsl:text>',targetModel='</xsl:text>                        
        <xsl:value-of select="concat($module-name,'.',$associationClassName)"/>
        <xsl:text>',</xsl:text>
        <xsl:if test="number($min) = 0">
            <xsl:text>blank=True,</xsl:text>
        </xsl:if>
        <!--
        <xsl:text>related_name='</xsl:text>
        <xsl:value-of select="lower-case(./UML:ModelElement.taggedValue/UML:TaggedValue[@tag='ea_targetName']/@value)"/>
        <xsl:text>_to_</xsl:text>
        <xsl:value-of select="lower-case($associationClassName)"/>
        <xsl:text>',</xsl:text>
        -->
        <xsl:text>)</xsl:text>
        <xsl:value-of select="$newline"/>
    </xsl:template>
    
    <xsl:template name="AttributeTemplate">
        <xsl:param name="min">1</xsl:param>
        <xsl:param name="max">1</xsl:param>
        <xsl:param name="parent"/>
        <xsl:param name="type"/>
        <xsl:param name="stereotype"/>
        <xsl:param name="documentation"/>

        <xsl:variable name="attributeName">
            <xsl:call-template name="UncapitalizeTemplate">
                <xsl:with-param name="string" select="@name"/>
            </xsl:call-template>
        </xsl:variable>
        
        <xsl:variable name="attributeID" select="./UML:StructuralFeature.type/UML:Classifier/@xmi.idref"/>
        <xsl:variable name="attributeClass" select="//UML:Class[@xmi.id=$attributeID]"/>
        
        <xsl:choose>
            <xsl:when test="$stereotype = 'unused'">
                <xsl:call-template name="CommentTemplate">
                    <xsl:with-param name="string">
                        <xsl:value-of select="$attributeName"/><xsl:text> is unused</xsl:text>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                
                <xsl:value-of select="concat($tab,$attributeName,' = ')"/>
                
                <xsl:variable name="externalGeneralisation"
                    select="$attributeClass/UML:ModelElement.taggedValue/UML:TaggedValue[@tag='genlinks'][1]"/>
                <xsl:variable name="simpleGeneralisation"
                    select="starts-with($externalGeneralisation/attribute::value,'Parent=xs:')"/>
                
                <xsl:choose>
                    <xsl:when test="$simpleGeneralisation">
                        <xsl:variable name="simpleType" select="$externalGeneralisation/@value"/>
                        <xsl:choose>
                            <xsl:when test="lower-case($simpleType)='xs:token;' or lower-case($simpleType)='xs:anysimpletype'">
                                <xsl:text>MetadataAtomicField.Factory("charfield",</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>SimpleType.Factory("</xsl:text>
                                <xsl:value-of select="$simpleType"/>
                                <xsl:text>,</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                    
                
                <xsl:choose>
                    <xsl:when test="lower-case($type)='integer'">
                        <xsl:text>MetadataAtomicField.Factory("integerfield",</xsl:text>                
                    </xsl:when>
                    <xsl:when test="lower-case($type)='characterstring' or lower-case($type)='string' or lower-case($type)='char'">
                        <xsl:text>MetadataAtomicField.Factory("charfield",</xsl:text>
                    </xsl:when>            
                    <xsl:when test="lower-case($type)='boolean'">
                        <xsl:text>MetadataAtomicField.Factory("booleanfield",</xsl:text>
                    </xsl:when>            
                    <xsl:when test="lower-case($type)='uri' or lower-case($type)='url'">
                        <xsl:text>MetadataAtomicField.Factory("urlfield",</xsl:text>
                    </xsl:when>            
                    <xsl:when test="lower-case($type)='date'">
                        <xsl:text>MetadataAtomicField.Factory("datefield",</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        
                        <xsl:variable name="attributeClass" select="//UML:Class[@name=$type]"/>
                        <xsl:variable name="attributeClassStereotype" select="$attributeClass/UML:ModelElement.stereotype/UML:Stereotype/@name"/>
                        <xsl:choose>
                            <xsl:when test="lower-case($attributeClassStereotype)='codelist' or lower-case($attributeClassStereotype)='enumeration'">
                                <xsl:text>MetadataEnumerationField(enumeration='</xsl:text>
                                <xsl:value-of select="concat($module-name,'.',$attributeClass/@name)"/>
                                <xsl:text>',</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:choose>
                                    <xsl:when test="number($max) &gt; 1">
                                        <xsl:text>MetadataManyToManyField(</xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:text>MetadataManyToOneField(</xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                                <xsl:text>sourceModel='</xsl:text>
                                <xsl:value-of select="concat($module-name,'.',$parent/@name)"/>
                                <xsl:text>',targetModel='</xsl:text>                        
                                <xsl:value-of select="concat($module-name,'.',$type)"/><!--$attributeClass/@name)"/>-->
                                <xsl:text>',</xsl:text>
                                <!--
                                <xsl:text>related_name='</xsl:text>
                                <xsl:value-of select="lower-case($parent/@name)"/>
                                <xsl:text>_to_</xsl:text>
                                <xsl:value-of select="lower-case($type)"/>
                                <xsl:text>',</xsl:text>
                                -->                                
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
                    </xsl:otherwise>
                </xsl:choose>
                
                <xsl:choose>
                    <xsl:when test="$min=0">
                        <xsl:text>blank=True,</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>blank=False,</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>)</xsl:text>
                <xsl:value-of select="$newline"/>
                <xsl:if test="$documentation">
                    <xsl:value-of select="concat($tab,$attributeName,'.help_text = ')"/>"<xsl:call-template name="DocumentationTemplate"><xsl:with-param name="string"><xsl:value-of select="$documentation"/></xsl:with-param></xsl:call-template>"
                </xsl:if>
                
            </xsl:otherwise>
        </xsl:choose>           
                    
    </xsl:template>
    
    <xsl:template name="DocumentationTemplate">
        <xsl:param name="string"/>
        
        <xsl:variable name="strippedNewLinesString" select="replace($string,'&#xA;','')"/>
        <xsl:variable name="strippedQuotesString" select="replace($strippedNewLinesString,'&quot;','')"/>

        <xsl:call-template name="StripHtmlTags">
            <xsl:with-param name="string" select="$strippedQuotesString"/>
        </xsl:call-template>
        
    </xsl:template>
    
    
    <!-- ********************* -->
    <!-- some helper templates -->
    <!-- ********************* -->
    
    <xsl:template name="LowerCaseTemplate">
        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,$upperCase,$lowerCase)"/>
    </xsl:template>
    
    <xsl:template name="UpperCaseTemplate">
        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,$lowerCase,$upperCase)"/>
    </xsl:template>    
    
    <xsl:template name="CapitalizeTemplate">
        <xsl:param name="string"/>
        <xsl:variable name="firstLetter">
            <xsl:call-template name="UpperCaseTemplate">
                <xsl:with-param name="string" select="substring($string,1,1)"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="concat($firstLetter,substring($string,2))"/>
    </xsl:template>
    
    <xsl:template name="UncapitalizeTemplate">
        <xsl:param name="string"/>
        <xsl:variable name="firstLetter">
            <xsl:call-template name="LowerCaseTemplate">
                <xsl:with-param name="string" select="substring($string,1,1)"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="concat($firstLetter,substring($string,2))"/>
    </xsl:template>
    
    <xsl:template name="StripHtmlTags">
        <xsl:param name="string"/>
                
        <xsl:choose>
            <xsl:when test="contains($string, '&lt;')">
                <xsl:value-of select="substring-before($string, '&lt;')"/>
                <xsl:call-template name="StripHtmlTags">
                    <xsl:with-param name="string" select="substring-after($string, '&gt;')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$string"/>
            </xsl:otherwise>
        </xsl:choose>        
    </xsl:template>
    
    <xsl:template name="StripNewLines">
        <xsl:param name="string"/>
        <xsl:value-of select="replace($string,'&#xA;','')"/>
    </xsl:template>
       
    <xsl:template name="SplitStringTemplate">
        <xsl:param name="string"/>
        <xsl:variable name="newlineSplitString" select="replace($string,'&#xA;','')"/>
        <xsl:variable name="underscoreSplitString" select="replace($newlineSplitString,'_',' ')"/>
        <xsl:variable name="hyphenSplitString" select="replace($underscoreSplitString,'-',' ')"/>
        <xsl:analyze-string select="$underscoreSplitString" regex="[a-z][A-Z]">
            <xsl:matching-substring>
                <xsl:value-of select="substring(.,1,1)"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="substring(.,2,1)"/>
            </xsl:matching-substring>
            <xsl:non-matching-substring>
                <xsl:value-of select="."/>
            </xsl:non-matching-substring>
        </xsl:analyze-string>
    </xsl:template>

    <xsl:template name="CommentTemplate">
        <xsl:param name="string"/>
        <xsl:value-of select="concat('# ',replace(replace($string,'&#xA;',' '),'^\s+',''),$newline)"/>
    </xsl:template>
    
</xsl:stylesheet>