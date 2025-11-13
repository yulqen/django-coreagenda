# Django-Coreagenda Tests

This directory contains comprehensive tests for the django-coreagenda package.

## Test Structure

```
tests/
├── conftest.py               # Pytest fixtures for all tests
├── settings.py               # Minimal Django settings for testing
├── README.md                 # This file
└── (test files in coreagenda/tests/)
```

## Running Tests

### Install Test Dependencies

```bash
pip install -e ".[dev]"
```

Or install requirements:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=coreagenda --cov-report=html
```

View coverage report at `htmlcov/index.html`.

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Workflow tests only
pytest -m workflow

# Slow tests
pytest -m slow
```

### Run Specific Test Files

```bash
# Test specific model
pytest coreagenda/tests/test_meeting_model.py

# Test specific service
pytest coreagenda/tests/test_services.py

# Test specific class
pytest coreagenda/tests/test_meeting_model.py::TestMeetingModel

# Test specific method
pytest coreagenda/tests/test_meeting_model.py::TestMeetingModel::test_create_meeting
```

### Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run Tests in Parallel

```bash
pytest -n auto  # Requires pytest-xdist
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Tests for individual model methods, properties, and basic functionality without complex interactions.

### Integration Tests (`@pytest.mark.integration`)
Tests for relationships between models, cascade deletes, and service interactions.

### Workflow Tests (`@pytest.mark.workflow`)
Tests for state machine transitions and workflow validations.

### Slow Tests (`@pytest.mark.slow`)
Tests that take longer to run (currently not used, reserved for future).

## Test Fixtures

All fixtures are defined in `tests/conftest.py`. Key fixtures include:

### User Fixtures
- `user` - Regular user
- `chairperson` - User who chairs meetings
- `note_taker` - User who takes notes
- `reviewer` - User who reviews agenda items
- `proposer` - User who proposes agenda items
- `multiple_users` - List of 5 users

### Meeting Fixtures
- `meeting` - Basic draft meeting
- `scheduled_meeting` - Published scheduled meeting
- `past_meeting` - Completed past meeting
- `full_meeting` - Complete meeting with all components

### AgendaItem Fixtures
- `agenda_item` - Draft agenda item
- `submitted_agenda_item` - Submitted agenda item
- `approved_agenda_item` - Approved agenda item
- `consent_agenda_item` - Consent agenda item
- `meeting_with_agenda` - Meeting with 3 approved items

### ActionItem Fixtures
- `action_item` - Basic assigned action
- `urgent_action_item` - Urgent priority action
- `overdue_action_item` - Overdue action

### Other Fixtures
- `minute` - Basic minute entry
- `decision_minute` - Decision minute with votes
- `attendance_record` - Attendance record
- `presenter` - Internal presenter
- `external_presenter` - External presenter
- `external_request` - Pending external request

## Writing Tests

### Example Test

```python
import pytest
from coreagenda.models import Meeting

@pytest.mark.unit
class TestMeetingModel:
    def test_create_meeting(self, chairperson):
        """Test creating a meeting."""
        meeting = Meeting.objects.create(
            title='Test Meeting',
            scheduled_date=timezone.now() + timedelta(days=7),
            chairperson=chairperson,
        )

        assert meeting.pk is not None
        assert meeting.title == 'Test Meeting'
```

### Testing Workflows

```python
@pytest.mark.workflow
def test_agenda_item_workflow(self, agenda_item, reviewer):
    """Test complete approval workflow."""
    # Start in draft
    assert agenda_item.status == 'draft'

    # Submit
    agenda_item.submit()
    assert agenda_item.status == 'submitted'

    # Approve
    agenda_item.approve(reviewer)
    assert agenda_item.status == 'approved'
```

### Using Fixtures

```python
def test_with_fixtures(self, meeting, agenda_item, user):
    """Fixtures are automatically created for each test."""
    assert agenda_item.meeting == meeting
    # Fixtures are isolated per test
```

## Test Coverage

Current test coverage includes:

- ✅ **Meeting Model**: Creation, methods, relationships, workflows
- ✅ **AgendaItem Model**: CRUD, state transitions, workflow validation
- ✅ **ActionItem Model**: CRUD, state transitions, overdue detection
- ✅ **Minute Model**: Recording, approval, decision tracking
- ✅ **AttendanceRecord Model**: Marking, late arrivals, departures
- ✅ **Presenter Model**: Internal/external, validation
- ✅ **ExternalRequest Model**: Workflow, agenda item creation
- ✅ **MeetingService**: All major operations
- ✅ **AgendaService**: Submission, review, organization
- ✅ **MinuteService**: Recording, approval, publishing
- ✅ **ActionService**: Creation, assignment, completion
- ✅ **AttendanceService**: Marking, tracking, reporting

## Continuous Integration

These tests are designed to run in CI environments:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pytest --cov=coreagenda --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Debugging Tests

### Print Debug Output

```python
def test_something(self, meeting):
    print(f"Meeting: {meeting}")  # Use -s flag to see output
    pytest coreagenda/tests/test_meeting_model.py -s
```

### Use pdb Debugger

```python
def test_something(self, meeting):
    import pdb; pdb.set_trace()
    # Code pauses here
```

### Show Local Variables

```bash
pytest -l  # Show local variables on failures
pytest -vv --tb=long  # Detailed tracebacks
```

## Best Practices

1. **Use descriptive test names**: `test_approve_submitted_agenda_item` not `test1`
2. **One assertion focus per test**: Tests should verify one behavior
3. **Use appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
4. **Keep tests isolated**: Don't rely on test execution order
5. **Use fixtures**: Don't create objects manually if a fixture exists
6. **Test edge cases**: Not just the happy path
7. **Test error conditions**: Verify exceptions are raised correctly

## Troubleshooting

### Database Errors

Tests use an in-memory SQLite database. If you see database errors:

```bash
# Clear any cached database
rm -f db.sqlite3

# Run migrations (shouldn't be needed for tests)
python manage.py migrate --settings=tests.settings
```

### Import Errors

Make sure django-coreagenda is installed in editable mode:

```bash
pip install -e .
```

### Fixture Not Found

Check `tests/conftest.py` for available fixtures. Fixtures must be defined before use.

## Contributing Tests

When adding new features:

1. Write tests first (TDD approach preferred)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov=coreagenda`
4. Add docstrings to test methods
5. Use appropriate markers
6. Update this README if adding new test categories

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Model Bakery](https://model-bakery.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
