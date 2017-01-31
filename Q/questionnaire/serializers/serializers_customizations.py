# from django.core.exceptions import ValidationError as DjangoValidationError
# from rest_framework.exceptions import ValidationError as RestValidationError
# from rest_framework import serializers
# from uuid import UUID as generate_uuid
#
# from Q.things.serializers.serializers_base import ThingListSerializer, ThingSerializer
# from Q.things.models.models_proxies import ThingProxyModel, ThingProxyCategory, ThingProxyProperty
#
#
# ################
# # base classes #
# ################
#
# class ThingProxySerializer(ThingSerializer):
#     pass
#
#
# class ThingProxyListSerializer(ThingListSerializer):
#     pass
#
# ####################
# # category classes #
# ####################
#
#
# class ThingProxyCategorySerializer(ThingProxySerializer):
#
#     class Meta:
#         model = ThingProxyCategory
#         list_serializer_class = ThingProxyListSerializer
#         fields = (
#             'id',
#             # 'guid',
#             'order',
#             'is_meta',
#             'name',
#             'documentation',
#             # these next fields are not part of the model
#             # but they can be used to facilitate ng interactivity on the client
#             'key',
#             'display_detail',
#         )
#
#     display_detail = serializers.SerializerMethodField(read_only=True)
#     key = serializers.SerializerMethodField(read_only=True)
#
#     # even though 'model_proxy' is a required field of the ThingProxyCategory model,
#     # it cannot possibly be set before the parent model_proxy itself has been saved;
#     # so I set 'allow_null' to True here...
#     model_proxy = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
#
#     def get_display_detail(self, obj):
#         """
#         not a _real_ field
#         just helps me w/ interactivity
#         I always load the customizer w/ display_detail = False
#         :param obj:
#         :return:
#         """
#         return False
#
#     def get_key(self, obj):
#         return obj.key
#
#     def to_internal_value(self, data):
#         internal_value = super(ThingListSerializer, self).to_internal_value(data)
#         # add the original key to use as guid so that a new key is not automatically generated
#         internal_value.update({
#             "guid": generate_uuid(data.get("key"))
#         })
#         pk = data.get("id")
#         if pk:
#             internal_value.update({
#                 "id": pk,  # put id back so that create/update will work for QListSerializer
#             })
#         return internal_value
#
#     def create(self, validated_data):
#         # validated_data = self.remove_superfluous_data(validated_data)
#         return super(ThingProxyCategorySerializer, self).create(validated_data)
#
#     def update(self, instance, validated_data):
#         # validated_data = self.remove_superfluous_data(validated_data)
#         return super(ThingProxyCategorySerializer, self).update(instance, validated_data)
#
#
# ####################
# # property classes #
# ####################
#
# class ThingProxyPropertySerializer(ThingProxySerializer):
#
#     class Meta:
#         model = ThingProxyProperty
#         list_serializer_class = ThingProxyListSerializer
#         fields = (
#                 'id',
#                 # 'guid',
#                 'order',
#                 'is_meta',
#                 'name',
#                 'documentation',
#                 # these next fields are not part of the model
#                 # but they can be used to facilitate ng interactivity on the client
#                 'key',
#                 'category_key',
#                 # 'display_detail',
#             )
#
#         key = serializers.SerializerMethodField(read_only=True, method_name="get_key")
#         category_key = serializers.SerializerMethodField(read_only=True, method_name="get_category_key")
#         display_detail = serializers.SerializerMethodField(read_only=True, method_name="get_display_detail")
#
#         # even though 'model_proxy' is a required field of the ThingProxyProperty model,
#         # it cannot possibly be set before the parent model_customization itself has been saved;
#         # so I set 'allow_null' to True here...
#         model_proxy = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
#
#         def get_key(self, obj):
#             return obj.key
#
#         def get_category_key(self, obj):
#             import ipdb; ipdb.set_trace()
#             return obj.category.key
#
#         def get_display_detail(self, obj):
#             """
#             not a _real_ field
#             just helps me w/ interactivity
#             :param obj:
#             :return:
#             """
#             return False
#
#         def to_internal_value(self, data):
#             internal_value = super(ThingProxyPropertySerializer, self).to_internal_value(data)
#
#             internal_value.update({
#                 "guid": generate_uuid(data.get("key")),
#                 # category_key would have been stripped out b/c it is not a real model field
#                 # I put it back here, in order to manipulate self.category in 'create/update' below
#                 "category_key": generate_uuid(data.get("category_key")),
#
#             })
#
#             pk = data.get("id")
#             if pk:
#                 internal_value.update({
#                     "id": pk,  # put id back so that update/create will work for ThingListSerializer
#                 })
#
#             return internal_value
#
#         def create(self, validated_data):
#
#             category_key = validated_data.pop("category_key", None)
#             category_proxy = ThingProxyCategory.objects.get_by_key(category_key)
#             validated_data["category_proxy"] = category_proxy
#
#             property_proxy = super(ThingProxyPropertySerializer, self).create(validated_data)
#
#             return property_proxy
#
#         def update(self, instance, validated_data):
#
#             # since I cannot change a property's category (as of v0.15), there is no need to re-set it here as above
#             # category_key = validated_data.pop("category_key", None)
#             # category_proxy = ThingProxyCategory.objects.get_by_key(category_key)
#             # validated_data["category_proxy"] = category_proxy
#
#             property_proxy = super(ThingProxyPropertySerializer, self).update(instance, validated_data)
#
#             return property_proxy
#
#
# #################
# # model classes #
# #################
#
#
# class ThingProxyModelSerializer(ThingProxySerializer):
#
#     class Meta:
#         model = ThingProxyModel
#         fields = (
#             'id',
#             # 'guid',
#             'order',
#             'is_meta',
#             'name',
#             'documentation',
#             'ontology',
#             'properties',
#             # these next fields are not part of the model
#             # but they can be used to facilitate ng interactivity on the client
#             'key',
#             'display_detail',
#         )
#
#         # there is no need to explicitly add QUniqueTogetherValidator
#         # b/c that is done automatically in "QSerializer.get_unique_together_validators()"
#         # validators = [
#         #     QUniqueTogetherValidator(
#         #         queryset=QModelCustomization.objects.all(),
#         #         # fields=('name', 'proxy', 'project'),
#         #     )
#         # ]
#
#     key = serializers.SerializerMethodField(read_only=True)  # name="get_key"
#     display_detail = serializers.SerializerMethodField(read_only=True)  # name="get_display_detail"
#
#     properties = ThingProxyPropertySerializer(many=True, required=False, source="property_proxies")
#
#     def get_key(self, obj):
#         return obj.key
#
#     def get_display_detail(self, obj):
#         """
#         not a _real_ field
#         just helps me w/ interactivity
#         :param obj:
#         :return:
#         """
#         return False
#
#
#     def create(self, validated_data):
#         """
#         ensures that nested fields are updated/created along w/ parent model
#         :param validated_data
#         :return the created model
#         """
#         # notice how all the calls to create are wrapped in a try/catch block;
#         # I translate every django error into a django-rest-framework error
#         # but, I still try to validate the rest of the data
#         # (this ensures _all_ errors will be caught)
#         # TODO: DOUBLE-CHECK THAT THIS WORKS IF THE ERROR MESSAGE IS NOT A LIST
#         # TODO: (B/C I THINK THAT DRF REQUIRES LISTS BUT DJANGO DOESN'T CARE)
#         validation_errors = RestValidationError({})
#
#         properties_serializer = self.fields["properties"]
#
#         properties_data = validated_data.pop(properties_serializer.source, [])
#
#         try:
#             model_proxy = ThingProxyModel.objects.create(**validated_data)
#         except DjangoValidationError as e:
#             model_proxy = None
#             validation_errors.detail.update(e.message_dict)
#
#         try:
#             for property_data in properties_data:
#                 property_data["model_proxy"] = model_proxy
#             properties_serializer.create(properties_data)
#         except DjangoValidationError as e:
#             validation_errors.detail.update(e.message_dict)
#
#         if len(validation_errors.detail):
#             raise validation_errors
#
#         return model_proxy
#
#     def update(self, instance, validated_data):
#         """
#         ensures that nested fields are updated/created along w/ parent model
#         :param instance:
#         :param validated_data:
#         :return:
#         """
#         # notice how all the calls to create or update are wrapped in a try/catch block;
#         # I translate every django error into a django-rest-framework error
#         # but, I still try to validate the rest of the data
#         # (this ensures _all_ errors will be caught)
#         # TODO: DOUBLE-CHECK THAT THIS WORKS IF THE ERROR MESSAGE IS NOT A LIST
#         # TODO: (B/C I THINK THAT DRF REQUIRES LISTS BUT DJANGO DOESN'T CARE)
#         validation_errors = RestValidationError({})
#
#         properties_serializer = self.fields["properties"]
#
#         properties_data = validated_data.pop(properties_serializer.source, instance.property_customizations.values())
#
#         try:
#             model_proxy = super(ThingProxyModel, self).update(instance, validated_data)
#         except DjangoValidationError as e:
#             validation_errors.detail.update(e.message_dict)
#
#         try:
#             properties_serializer.update(model_proxy.property_customizations.all(), properties_data)
#         except DjangoValidationError as e:
#             validation_errors.detail.update(e.message_dict)
#
#         if len(validation_errors.detail):
#             raise validation_errors
#
#         return model_proxy