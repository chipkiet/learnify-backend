from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

# import user thẳng sẽ tạo dêpndency cứng , get_uset_model đọc authmodel từ settings.py ( có thể tuỳ chỉnh = nó như dependency injection vậy)

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer): 
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    class Meta: 
        model = User
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # User.objects = UserManager()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    # chỉ nhận, không trả ra gì cả 
    # Request:  { email, password, full_name }
    # Response: { email, full_name } ( không trả password về )

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
        # validate_password là hàm có sẵn của django 
    )


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "avatar",
            "phone_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["email", "created_at", "updated_at"]
