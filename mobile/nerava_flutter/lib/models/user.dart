import 'package:json_annotation/json_annotation.dart';

part 'user.g.dart';

@JsonSerializable()
class User {
  final int id;
  final String email;
  @JsonKey(name: 'display_name')
  final String? displayName;
  @JsonKey(name: 'role_flags')
  final String? roleFlags;
  @JsonKey(name: 'linked_merchant')
  final LinkedMerchant? linkedMerchant;

  User({
    required this.id,
    required this.email,
    this.displayName,
    this.roleFlags,
    this.linkedMerchant,
  });

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);

  String get displayNameOrEmail => displayName ?? email;
}

@JsonSerializable()
class LinkedMerchant {
  final int id;
  final String name;
  @JsonKey(name: 'nova_balance')
  final int? novaBalance;

  LinkedMerchant({
    required this.id,
    required this.name,
    this.novaBalance,
  });

  factory LinkedMerchant.fromJson(Map<String, dynamic> json) =>
      _$LinkedMerchantFromJson(json);
  Map<String, dynamic> toJson() => _$LinkedMerchantToJson(this);
}

