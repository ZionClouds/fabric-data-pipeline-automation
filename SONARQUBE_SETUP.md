# SonarQube Integration Setup Guide

This document explains the SonarQube integration that has been added to your Fabric Data Pipeline Automation project.

## Changes Made

### 1. Updated GitHub Actions Workflow
**File:** `.github/workflows/azure-container-deploy.yml`

Added a new `SonarQubeAnalysis` job that:
- Runs on every push and pull request to `main` branch
- Downloads and installs SonarQube Scanner
- Scans the entire codebase (both backend and frontend)
- Sends analysis results to your SonarQube server

**Job Location:** Runs after `CodeTesting` and before `BackendDeployment`

### 2. Created SonarQube Configuration
**File:** `sonar-project.properties`

Configures SonarQube analysis with:
- **Project Key:** `fabric-pipeline-automation`
- **Source Directories:** `backend` and `frontend/src`
- **Test Directories:** `backend/tests`
- **Language Support:** Python 3.11 and JavaScript/TypeScript
- **Coverage Reports:** Python coverage XML and JavaScript LCOV
- **Exclusions:** node_modules, build artifacts, test files, etc.

### 3. Created SonarQube Ignore File
**File:** `.sonarignore`

Explicitly excludes:
- Dependencies (node_modules, venv)
- Build outputs (build/, dist/)
- Test coverage files
- IDE files
- Logs and environment files
- Docker and CI/CD configuration files

## What You Need to Do

### Step 1: Set Up SonarQube Server

If you don't already have a SonarQube server, you have two options:

#### Option A: Use SonarCloud (Cloud-based, Free for Open Source)
1. Go to https://sonarcloud.io/
2. Sign up with your GitHub account
3. Create a new organization (or use existing)
4. Note down your:
   - **SONAR_HOST_URL:** `https://sonarcloud.io`
   - **SONAR_TOKEN:** Generate from Account > Security > Generate Tokens

#### Option B: Self-Hosted SonarQube
1. Install SonarQube on your server (Docker recommended)
2. Create a new project in SonarQube UI
3. Note down your:
   - **SONAR_HOST_URL:** Your SonarQube server URL (e.g., `https://sonar.yourcompany.com`)
   - **SONAR_TOKEN:** Generate from My Account > Security > Generate Tokens

### Step 2: Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add these two secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SONAR_HOST_URL` | Your SonarQube server URL | Example: `https://sonarcloud.io` or `https://sonar.yourcompany.com` |
| `SONAR_TOKEN` | Your SonarQube authentication token | Generated from SonarQube dashboard |

### Step 3: Create Project in SonarQube (If using SonarCloud)

1. Log in to SonarCloud
2. Click **+** > **Analyze new project**
3. Select your GitHub organization and repository
4. Follow the wizard to complete setup
5. Use the project key: `fabric-pipeline-automation`

### Step 4: Test the Integration

1. Commit and push these changes to your repository:
   ```bash
   git add .
   git commit -m "Add SonarQube integration"
   git push origin main
   ```

2. Go to **Actions** tab in GitHub to see the workflow run
3. Check the `SonarQubeAnalysis` job for results
4. View detailed analysis in your SonarQube dashboard

## SonarQube Analysis Details

### What Gets Analyzed

**Backend (Python):**
- All Python files in `backend/` directory
- Excludes: tests, migrations, settings.py, __pycache__
- Checks for: bugs, vulnerabilities, code smells, security hotspots
- Python version: 3.11

**Frontend (JavaScript/React):**
- All JavaScript/TypeScript files in `frontend/src/`
- Excludes: node_modules, build/, tests, minified files
- Checks for: bugs, vulnerabilities, code smells, duplications

### Quality Metrics Tracked

- **Reliability:** Bugs and reliability rating
- **Security:** Vulnerabilities and security rating
- **Maintainability:** Code smells and technical debt
- **Coverage:** Test coverage percentage
- **Duplications:** Duplicated code blocks
- **Complexity:** Cyclomatic complexity

## Viewing SonarQube Results

### In GitHub Actions
- Go to **Actions** tab
- Click on any workflow run
- Expand the `SonarQubeAnalysis` job
- View scan logs and status

### In SonarQube Dashboard
- Log in to your SonarQube server
- Navigate to your project: `fabric-pipeline-automation`
- View:
  - **Overview:** Quality gate status, coverage, duplications
  - **Issues:** List of bugs, vulnerabilities, code smells
  - **Measures:** Detailed metrics and trends
  - **Code:** Browse code with inline annotations

## Customizing SonarQube Analysis

### Modify Analysis Scope

Edit `sonar-project.properties` to:
- Change source directories
- Add/remove exclusions
- Configure language-specific settings
- Set quality gate thresholds

### Add More Language Support

For additional languages, update `sonar-project.properties`:
```properties
# For TypeScript
sonar.typescript.lcov.reportPaths=coverage/lcov.info

# For Java
sonar.java.binaries=target/classes
```

### Configure Quality Gates

In SonarQube dashboard:
1. Go to **Quality Gates**
2. Create custom quality gate or use default
3. Set thresholds for:
   - Coverage (e.g., > 80%)
   - Duplications (e.g., < 3%)
   - Bugs (e.g., = 0)
   - Vulnerabilities (e.g., = 0)

## Troubleshooting

### Issue: "Shallow clone detected"
**Solution:** The workflow already includes `fetch-depth: 0` to perform a full clone.

### Issue: "Authentication failed"
**Solution:**
- Verify `SONAR_TOKEN` is correctly set in GitHub Secrets
- Check token hasn't expired in SonarQube
- Regenerate token if necessary

### Issue: "Project key already exists"
**Solution:**
- Use a unique project key in `sonar-project.properties`
- Or delete the existing project in SonarQube

### Issue: "No coverage report found"
**Solution:**
- Ensure tests are running before SonarQube analysis
- Check coverage report paths in `sonar-project.properties`
- Verify coverage files are generated during test execution

## Additional Resources

- [SonarQube Documentation](https://docs.sonarqube.org/latest/)
- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [SonarScanner for GitHub Actions](https://github.com/SonarSource/sonarqube-scan-action)
- [Python Analysis Parameters](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [JavaScript Analysis Parameters](https://docs.sonarqube.org/latest/analysis/languages/javascript/)

## Support

For issues or questions:
1. Check SonarQube community forum
2. Review workflow logs in GitHub Actions
3. Consult your organization's SonarQube administrator
