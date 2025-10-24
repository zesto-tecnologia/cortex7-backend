#!/bin/bash

# Comprehensive test runner script for all services
# This script runs unit tests for all critical endpoints in the system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_header() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check if dependencies are installed
check_dependencies() {
    print_header "🔍 Checking Dependencies"

    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    else
        PYTHON_VERSION=$(python3 --version)
        print_success "Python installed: $PYTHON_VERSION"
    fi

    # Check for pytest
    if ! python3 -m pytest --version &> /dev/null; then
        print_warning "pytest not installed. Installing..."
        pip install pytest pytest-asyncio pytest-cov pytest-mock
    else
        PYTEST_VERSION=$(python3 -m pytest --version | head -1)
        print_success "pytest installed: $PYTEST_VERSION"
    fi

    # Check for required test dependencies
    python3 -c "import aiosqlite" 2>/dev/null || pip install aiosqlite
    python3 -c "import faker" 2>/dev/null || pip install faker

    echo ""
}

# Function to run tests for a specific service
run_service_tests() {
    local service=$1
    local test_path=$2

    print_info "Testing $service Service..."

    if [ -f "$test_path" ]; then
        # Run the tests with coverage
        if python3 -m pytest "$test_path" -v --tb=short --cov="services/$service" --cov-report=term-missing; then
            print_success "$service Service tests passed!"
            return 0
        else
            print_error "$service Service tests failed!"
            return 1
        fi
    else
        print_warning "Test file not found: $test_path"
        return 2
    fi
}

# Function to run all tests
run_all_tests() {
    print_header "🚀 Running All Unit Tests"

    local total_services=0
    local passed_services=0
    local failed_services=0
    local skipped_services=0

    # Test each service
    services=("financial" "hr" "legal" "procurement" "documents" "ai")
    service_names=("Financial" "HR" "Legal" "Procurement" "Documents" "AI")
    test_files=("tests/financial/test_financial_endpoints.py" "tests/hr/test_hr_endpoints.py" "tests/legal/test_legal_endpoints.py" "tests/procurement/test_procurement_endpoints.py" "tests/documents/test_documents_endpoints.py" "tests/ai/test_ai_endpoints.py")

    # Run tests for each service
    for i in ${!services[@]}; do
        echo ""
        total_services=$((total_services + 1))

        if run_service_tests "${services[$i]}" "${test_files[$i]}"; then
            passed_services=$((passed_services + 1))
        else
            if [ $? -eq 2 ]; then
                skipped_services=$((skipped_services + 1))
            else
                failed_services=$((failed_services + 1))
            fi
        fi

        echo ""
    done

    # Run tests for existing auth service if available
    if [ -d "services/auth/tests" ]; then
        echo ""
        print_info "Testing Auth Service (existing tests)..."
        total_services=$((total_services + 1))

        if python3 -m pytest services/auth/tests/ -v --tb=short; then
            print_success "Auth Service tests passed!"
            passed_services=$((passed_services + 1))
        else
            print_error "Auth Service tests failed!"
            failed_services=$((failed_services + 1))
        fi
    fi

    return $failed_services
}

# Function to generate test report
generate_test_report() {
    local failed_count=$1

    print_header "📊 Test Summary Report"

    REPORT_FILE="tests/TEST_RESULTS_$(date +%Y%m%d_%H%M%S).md"

    cat > "$REPORT_FILE" << EOF
# Unit Test Results Report

## Test Execution Date: $(date)

## Summary

- **Total Services Tested**: $total_services
- **Passed**: $passed_services
- **Failed**: $failed_services
- **Skipped**: $skipped_services

## Service Test Results

| Service | Status | Coverage |
|---------|--------|----------|
| Financial | $([ -f tests/financial/test_financial_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| HR | $([ -f tests/hr/test_hr_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| Legal | $([ -f tests/legal/test_legal_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| Procurement | $([ -f tests/procurement/test_procurement_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| Documents | $([ -f tests/documents/test_documents_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| AI | $([ -f tests/ai/test_ai_endpoints.py ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |
| Auth | $([ -d services/auth/tests ] && echo "✅ Tested" || echo "⚠️ Skipped") | - |

## Test Coverage

Run with coverage report to get detailed metrics.

## Recommendations

1. **Coverage Goals**: Aim for at least 80% code coverage
2. **Integration Tests**: Add integration tests for service interactions
3. **Performance Tests**: Consider adding performance benchmarks
4. **End-to-End Tests**: Implement E2E tests for critical workflows

## Next Steps

1. Fix any failing tests
2. Add missing test cases for edge scenarios
3. Implement integration tests
4. Set up CI/CD pipeline for automated testing
EOF

    print_success "Test report generated: $REPORT_FILE"

    if [ $failed_count -eq 0 ]; then
        print_success "All tests passed successfully! 🎉"
        return 0
    else
        print_error "$failed_count service(s) had failing tests"
        return 1
    fi
}

# Main execution
main() {
    print_header "🧪 Cortex Backend Unit Testing Suite"
    echo "Testing all critical service endpoints after PT→EN refactoring"
    echo ""

    # Check dependencies
    check_dependencies

    # Set Python path
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"

    # Run all tests
    run_all_tests
    failed_count=$?

    # Generate report
    generate_test_report $failed_count

    echo ""
    print_header "📈 Testing Complete"

    if [ $failed_count -eq 0 ]; then
        print_success "All services are functioning correctly!"
        print_info "You can now proceed with confidence that the system is stable."
    else
        print_warning "Some tests failed. Please review the errors above."
        print_info "Fix the failing tests before proceeding to production."
    fi

    exit $failed_count
}

# Parse command line arguments
case "${1:-}" in
    --service)
        # Run tests for a specific service
        if [ -z "$2" ]; then
            print_error "Please specify a service name"
            exit 1
        fi

        export PYTHONPATH="${PYTHONPATH}:$(pwd)"

        case "$2" in
            financial)
                run_service_tests "financial" "tests/financial/test_financial_endpoints.py"
                ;;
            hr)
                run_service_tests "hr" "tests/hr/test_hr_endpoints.py"
                ;;
            legal)
                run_service_tests "legal" "tests/legal/test_legal_endpoints.py"
                ;;
            procurement)
                run_service_tests "procurement" "tests/procurement/test_procurement_endpoints.py"
                ;;
            documents)
                run_service_tests "documents" "tests/documents/test_documents_endpoints.py"
                ;;
            ai)
                run_service_tests "ai" "tests/ai/test_ai_endpoints.py"
                ;;
            auth)
                run_service_tests "auth" "services/auth/tests/"
                ;;
            *)
                print_error "Unknown service: $2"
                print_info "Available services: financial, hr, legal, procurement, documents, ai, auth"
                exit 1
                ;;
        esac
        ;;
    --coverage)
        # Run tests with detailed coverage report
        export PYTHONPATH="${PYTHONPATH}:$(pwd)"
        print_header "Running tests with coverage report"
        python3 -m pytest tests/ services/auth/tests/ --cov=services --cov-report=html --cov-report=term
        print_info "Coverage report generated in htmlcov/index.html"
        ;;
    --quick)
        # Run quick smoke tests
        export PYTHONPATH="${PYTHONPATH}:$(pwd)"
        print_header "Running quick smoke tests"
        python3 -m pytest tests/ -k "test_health_check" -v
        ;;
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  (no args)       Run all unit tests"
        echo "  --service NAME  Run tests for a specific service"
        echo "  --coverage      Run tests with coverage report"
        echo "  --quick         Run quick smoke tests"
        echo "  --help          Show this help message"
        echo ""
        echo "Services: financial, hr, legal, procurement, documents, ai, auth"
        ;;
    *)
        # Run all tests by default
        main
        ;;
esac