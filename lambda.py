import boto3
import chardet  # Veya charset_normalizer, hangisini kullanıyorsanız onu ekleyin.
from botocore.exceptions import NoCredentialsError

# AWS Servislerini başlat
s3_client = boto3.client('s3')
ses_client = boto3.client('ses', region_name='eu-west-1')

# Lambda fonksiyonu
def lambda_handler(event, context):
    try:
        # Bucket adı
        bucket_name = 'python-log'
        
        # Bucket'taki objeleri listele
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            return {'statusCode': 404, 'body': 'Bucket boş.'}
        
        # En son eklenen .txt dosyasını bul
        txt_files = [obj for obj in response['Contents'] if obj['Key'].endswith('.txt')]
        if not txt_files:
            return {'statusCode': 404, 'body': 'Hiç .txt dosyası bulunamadı.'}
        
        latest_file = max(txt_files, key=lambda x: x['LastModified'])
        file_key = latest_file['Key']
        
        # Dosya içeriğini oku
        file_obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        raw_content = file_obj['Body'].read()

        # Kodlamayı algıla ve dönüştür
        detected_encoding = chardet.detect(raw_content)['encoding']
        if not detected_encoding:
            detected_encoding = 'utf-8'  # Varsayılan olarak UTF-8 kullan
        file_content = raw_content.decode(detected_encoding)
        
        # E-posta detayları
        sender_email = "info@turins-dev.eu-west-1.aws.pmicloud.biz"
        recipient_email = "goker.inel@contracted.pmi.com"
        subject = f"En Son Yüklenen Dosya: {file_key}"
        body_text = f"Merhaba,\n\nS3 bucket'ınıza yüklenen en son dosyanın içeriği aşağıdadır:\n\n{file_content}"
        
        # E-postayı gönder
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [recipient_email],
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                },
            },
        )
        
        return {'statusCode': 200, 'body': f"E-posta başarıyla gönderildi: {response['MessageId']}"}
    
    except NoCredentialsError:
        return {'statusCode': 401, 'body': 'AWS kimlik bilgileri eksik.'}
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}
