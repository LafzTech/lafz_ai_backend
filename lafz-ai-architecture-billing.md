# Lafz AI - Complete Architecture & Setup Guide

## 🏗️ Recommended Architecture (Optimized)

### Phase 1: MVP (Single Cloud - Firebase Focused)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flutter App   │    │   Firebase Auth  │    │   Cloud Storage │
│                 │◄──►│   Firestore DB   │◄──►│   (File Upload) │
│                 │    │   Cloud Functions│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Vertex AI      │
                       │   (Document AI)  │
                       └──────────────────┘
```

### Phase 2: Scale (Hybrid Approach)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flutter App   │    │   Firebase       │    │   GCS + S3      │
│                 │◄──►│   + FastAPI      │◄──►│   (Multi-region)│
│                 │    │   + Cloud Run    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Cloud Tasks    │
                       │   + AI Pipeline  │
                       └──────────────────┘
```

## 🛠️ Technology Stack

### Frontend
- **Flutter** (Web + Mobile)
- **Firebase SDK** (Auth, Firestore, Storage)

### Backend (MVP)
- **Firebase Functions** (Node.js/Python)
- **Firestore** (Multi-tenant with collection groups)
- **Firebase Auth** (Multi-tenant)
- **Cloud Storage** (File uploads)
- **Vertex AI** (Document processing)

### Backend (Scale)
- **Cloud Run** (FastAPI)
- **Cloud Tasks** (Async processing)
- **AlloyDB/PostgreSQL** (Core system data)
- **Redis** (Caching)

### DevOps & Infrastructure
- **Terraform** (Infrastructure as Code)
- **GitHub Actions** (CI/CD)
- **Cloud Build** (Container builds)
- **Cloud Monitoring** (Observability)

## 🚀 Project Structure

```
lafz-ai/
├── frontend/                 # Flutter application
│   ├── lib/
│   ├── pubspec.yaml
│   └── firebase_options.dart
├── backend/
│   ├── functions/           # Firebase Functions
│   ├── api/                # FastAPI (Phase 2)
│   └── shared/             # Shared utilities
├── infrastructure/
│   ├── terraform/
│   ├── scripts/
│   └── config/
├── docs/
└── docker-compose.yml      # Local development
```

## 📋 Prerequisites

### Required Tools
```bash
# Install Flutter
curl -fsSL https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.16.0-stable.tar.xz | tar xJ
export PATH="$PATH:`pwd`/flutter/bin"

# Install Firebase CLI
npm install -g firebase-tools

# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Required Accounts
- Google Cloud Platform account
- Firebase project
- GitHub account (for CI/CD)

## 🎯 Phase 1: MVP Setup (30 minutes)

### Step 1: Initialize Firebase Project

```bash
# Login to Firebase
firebase login

# Create new project
firebase projects:create lafz-ai-mvp

# Initialize Firebase in your project
cd lafz-ai
firebase init

# Select:
# - Functions (Node.js)
# - Firestore
# - Storage
# - Hosting
```

### Step 2: Flutter Setup

```bash
# Create Flutter project
flutter create frontend
cd frontend

# Add Firebase dependencies
flutter pub add firebase_core firebase_auth cloud_firestore firebase_storage

# Configure Firebase
flutterfire configure
```

### Step 3: Firestore Multi-tenant Structure

```javascript
// functions/index.js
const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp();
const db = admin.firestore();

// Collection structure per tenant
// companies/{companyId}/products/{productId}
// companies/{companyId}/customers/{customerId}
// companies/{companyId}/invoices/{invoiceId}

exports.createCompany = functions.https.onCall(async (data, context) => {
  const { name, email, gst } = data;
  const companyRef = db.collection('companies').doc();
  
  await companyRef.set({
    name,
    email,
    gst,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
    status: 'active'
  });
  
  return { companyId: companyRef.id };
});
```

### Step 4: Document Processing Function

```python
# functions/main.py (Python)
from firebase_functions import https_fn
from google.cloud import documentai
import pandas as pd

@https_fn.on_call()
def process_document(req):
    file_uri = req.data['file_uri']
    company_id = req.data['company_id']
    
    # Process with Document AI
    client = documentai.DocumentProcessorServiceClient()
    # ... document processing logic
    
    # Save to Firestore
    # ... save processed data
    
    return {"status": "success"}
```

### Step 5: Security Rules

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Companies can only access their own data
    match /companies/{companyId}/{document=**} {
      allow read, write: if request.auth != null 
        && request.auth.token.company_id == companyId;
    }
    
    // Super admin access
    match /{document=**} {
      allow read, write: if request.auth != null 
        && request.auth.token.admin == true;
    }
  }
}
```

## 🔄 Phase 2: Production Ready (Terraform)

### Infrastructure Setup

```hcl
# infrastructure/terraform/main.tf
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Firebase project
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id
}

# Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_firebase_project.default]
}

# Cloud Run service
resource "google_cloud_run_service" "api" {
  name     = "lafz-ai-api"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/lafz-ai-api:latest"
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
      }
    }
  }
}
```

### Variables

```hcl
# infrastructure/terraform/variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Firebase

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.16.0'
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend && flutter pub get
        cd backend/functions && npm install
    
    - name: Run tests
      run: |
        cd frontend && flutter test
        cd backend/functions && npm test
    
    - name: Build Flutter Web
      run: cd frontend && flutter build web
    
    - name: Deploy to Firebase
      uses: FirebaseExtended/action-hosting-deploy@v0
      with:
        repoToken: '${{ secrets.GITHUB_TOKEN }}'
        firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
        projectId: lafz-ai-mvp
```

## 📊 Monitoring & Observability

### Error Tracking

```javascript
// functions/index.js
const { ErrorReporting } = require('@google-cloud/error-reporting');
const errors = new ErrorReporting();

exports.processDocument = functions.https.onCall(async (data, context) => {
  try {
    // Your function logic
  } catch (error) {
    errors.report(error);
    throw new functions.https.HttpsError('internal', 'Processing failed');
  }
});
```

### Performance Monitoring

```dart
// frontend/lib/main.dart
import 'package:firebase_performance/firebase_performance.dart';

class DocumentService {
  static Future<void> uploadDocument(File file) async {
    final trace = FirebasePerformance.instance.newTrace('document_upload');
    await trace.start();
    
    try {
      // Upload logic
      await FirebaseStorage.instance.ref().putFile(file);
    } finally {
      await trace.stop();
    }
  }
}
```

## 🧪 Local Development

### Docker Compose for Backend Services

```yaml
# docker-compose.yml
version: '3.8'

services:
  firebase-emulator:
    image: gcr.io/firebase-tools
    ports:
      - "4000:4000"  # Emulator UI
      - "8080:8080"  # Firestore
      - "9000:9000"  # Storage
      - "5001:5001"  # Functions
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: firebase emulators:start --import=./emulator-data
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Development Scripts

```bash
#!/bin/bash
# scripts/dev-setup.sh

echo "🚀 Setting up Lafz AI development environment..."

# Install dependencies
echo "📦 Installing Flutter dependencies..."
cd frontend && flutter pub get && cd ..

echo "📦 Installing Functions dependencies..."
cd backend/functions && npm install && cd ../..

# Start emulators
echo "🔥 Starting Firebase emulators..."
firebase emulators:start --import=./emulator-data

echo "✅ Development environment ready!"
echo "   - Firebase UI: http://localhost:4000"
echo "   - Flutter app: flutter run -d chrome"
```

## 🔐 Security Best Practices

### Environment Variables

```bash
# .env.example
PROJECT_ID=lafz-ai-mvp
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=lafz-ai-mvp.firebaseapp.com
STORAGE_BUCKET=lafz-ai-mvp.appspot.com

# Production secrets (use Secret Manager)
OPENAI_API_KEY=secret-key
DATABASE_URL=secret-url
```

### Security Rules Testing

```javascript
// firestore-test.js
const firebase = require('firebase/compat/app');
require('firebase/compat/firestore');

describe('Firestore Security Rules', () => {
  test('Users can only access their company data', async () => {
    const db = firebase.firestore();
    const testDoc = db.collection('companies').doc('company1').collection('products').doc('test');
    
    await firebase.auth().signInWithCustomToken(createMockToken({ company_id: 'company1' }));
    await expect(testDoc.get()).resolves.toBeDefined();
    
    await firebase.auth().signInWithCustomToken(createMockToken({ company_id: 'company2' }));
    await expect(testDoc.get()).rejects.toThrow();
  });
});
```

## 📈 Scaling Considerations

### Database Optimization

```javascript
// Composite indexes for common queries
// firestore.indexes.json
{
  "indexes": [
    {
      "collectionGroup": "invoices",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "companyId", "order": "ASCENDING" },
        { "fieldPath": "date", "order": "DESCENDING" }
      ]
    }
  ]
}
```

### Caching Strategy

```dart
// frontend/lib/services/cache_service.dart
class CacheService {
  static const _cache = <String, dynamic>{};
  
  static Future<T?> get<T>(String key) async {
    return _cache[key] as T?;
  }
  
  static Future<void> set<T>(String key, T value, {Duration? ttl}) async {
    _cache[key] = value;
    if (ttl != null) {
      Timer(ttl, () => _cache.remove(key));
    }
  }
}
```

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Security rules tested
- [ ] Performance tests passed
- [ ] Error handling implemented
- [ ] Monitoring configured

### Post-deployment
- [ ] Health checks passing
- [ ] Error rates normal
- [ ] Performance metrics green
- [ ] User acceptance testing
- [ ] Backup procedures verified

## 📚 Additional Resources

### Documentation Links
- [Firebase Documentation](https://firebase.google.com/docs)
- [Flutter Documentation](https://docs.flutter.dev)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### Useful Commands
```bash
# Deploy functions only
firebase deploy --only functions

# Deploy with specific target
firebase deploy --only hosting:production

# View logs
firebase functions:log

# Local development
flutter run -d chrome --web-port 3000
```

## 🎯 Success Metrics

### Technical KPIs
- **App Load Time**: < 3 seconds
- **Document Processing**: < 30 seconds
- **Uptime**: > 99.9%
- **Error Rate**: < 0.1%

### Business KPIs
- **User Onboarding**: < 5 minutes
- **Document Upload Success**: > 95%
- **User Retention**: Track weekly active users
- **Feature Adoption**: Track invoice generation usage