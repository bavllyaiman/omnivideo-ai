# OmniVideo AI - Free Deployment Guide

## كل مجاني 100% - لا يحتاج بطاقة ائتمان

---

## الخطوة 1: حسابات مجانية

### 1. Neon PostgreSQL (قاعدة بيانات مجانية)
1. ادخل https://neon.tech
2. سجّل بحساب Google
3. اضغط "Create Project"
4. انسخ **Connection string** (يبدأ بـ `postgresql://...`)
5. خزّنه للمعادلة

### 2. Cloudflare R2 (تخزين مجاني 10GB)
1. ادخل https://dash.cloudflare.com
2. سجّل حساب مجاني
3. اذهب إلى R2 Object Storage
4. اضغط "Create Bucket" → اسم: `omnivideo`
5. اذهب إلى "Manage R2 API Tokens" → "Create API Token"
6. انسخ:
   - Account ID
   - Access Key ID
   - Secret Access Key
   - Endpoint URL

### 3. Oracle Cloud Free Tier (سيرفر مجاني دائماً)
1. ادخل https://cloud.oracle.com/free
2. سجّل حساب مجاني (يحتاج بطاقة لكن لا يشحن)
3. اختر "Create a VM Instance"
4. اختر "Always Free" → ARM shape (4 cores, 24GB RAM)
5. اختر Ubuntu 22.04
6. سجّل الدخول بـ SSH

---

## الخطوة 2: نشر الـ Backend على Vercel

```bash
cd backend
# أضف المتغيرات على Vercel:
npx vercel env add DATABASE_URL production
# الصق Connection string من Neon

npx vercel env add JWT_SECRET_KEY production
# اكتب أي كلمة سر طويلة

npx vercel env add WORKER_URL production
# الصق رابط الـ Worker (من الخطوة 3)

npx vercel env add AWS_ACCESS_KEY_ID production
# الصق Access Key من Cloudflare R2

npx vercel env add AWS_SECRET_ACCESS_KEY production
# الصق Secret Key من Cloudflare R2

npx vercel env add AWS_S3_BUCKET production
# اكتب: omnivideo

npx vercel env add AWS_S3_ENDPOINT_URL production
# الصق Endpoint من Cloudflare R2

npx vercel --yes --prod
```

---

## الخطوة 3: نشر الـ Worker على Oracle Cloud

```bash
# اتصل بالسيرفر:
ssh ubuntu@<YOUR_SERVER_IP>

# ثبّت Docker:
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# انسخ المشروع:
git clone https://github.com/bavllyaiman/omnivideo-ai.git
cd omnivideo-ai/worker

# أنشئ ملف .env:
cat > .env << 'EOF'
AWS_S3_ENDPOINT_URL=https://<YOUR_R2_ENDPOINT>
AWS_ACCESS_KEY_ID=<YOUR_R2_ACCESS_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_R2_SECRET_KEY>
AWS_S3_BUCKET=omnivideo
AWS_S3_REGION=auto
API_URL=https://backend-black-three-69.vercel.app
EOF

# شغّل الـ Worker:
docker-compose up -d

# تأكد إنه شغال:
curl http://localhost:8001/health
```

---

## الخطوة 4: وصل Frontend بالـ Worker

```bash
cd frontend
npx vercel env add NEXT_PUBLIC_API_URL production
# الصق رابط Backend

npx vercel --yes --prod
```

---

## الروابط

| الخدمة | الرابط |
|--------|--------|
| الموقع | https://frontend-ashen-three-14.vercel.app |
| API Docs | https://backend-black-three-69.vercel.app/docs |
| GitHub | https://github.com/bavllyaiman/omnivideo-ai |

---

## أوامر مفيدة

```bash
# تحقق من Worker:
curl https://<YOUR_SERVER_IP>:8001/health

# تحقق من Backend:
curl https://backend-black-three-69.vercel.app/api/health
```
