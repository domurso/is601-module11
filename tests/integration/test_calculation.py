import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from datetime import datetime
from app.models.calculations import Calculation, Base
from app.schemas.calculation import CalculationCreate, CalculationRead, CalculationType
from app.models.user import User

# Set up in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db():
    """Provide a database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db):
    """Create a test user for foreign key reference."""
    user = User(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        username="johndoe",
        password=User.hash_password("SecurePass123"),
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    return user

# Tests for CalculationCreate Schema
def test_calculation_create_valid():
    """Test CalculationCreate with valid data."""
    data = {"a": 10.0, "b": 5.0, "type": "add"}
    calc = CalculationCreate(**data)
    assert calc.a == 10.0
    assert calc.b == 5.0
    assert calc.type == CalculationType.ADD

def test_calculation_create_invalid_type():
    """Test CalculationCreate with invalid calculation type."""
    data = {"a": 10.0, "b": 5.0, "type": "invalid"}
    with pytest.raises(ValidationError, match="Input should be 'add', 'subtract', 'multiply' or 'divide'"):
        CalculationCreate(**data)

def test_calculation_create_divide_by_zero():
    """Test CalculationCreate with b=0 for divide type."""
    data = {"a": 10.0, "b": 0.0, "type": "divide"}
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationCreate(**data)

def test_calculation_create_invalid_numeric_input():
    """Test CalculationCreate with non-numeric a or b."""
    data = {"a": "invalid", "b": 5.0, "type": "add"}
    with pytest.raises(ValidationError, match="Input should be a valid number"):
        CalculationCreate(**data)

# Tests for CalculationRead Schema
def test_calculation_read_valid():
    """Test CalculationRead with valid data."""
    data = {
        "id": uuid4(),
        "user_id": uuid4(),
        "a": 10.0,
        "b": 5.0,
        "type": "add",
        "result": 15.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    calc = CalculationRead(**data)
    assert calc.a == 10.0
    assert calc.b == 5.0
    assert calc.type == CalculationType.ADD
    assert calc.result == 15.0

# Tests for Calculation Model
def test_calculation_model_add(db, test_user):
    """Test creating a calculation with 'add' type."""
    calc = Calculation.create_calculation(
        db=db,
        user_id=test_user.id,
        a=10.0,
        b=5.0,
        calc_type="add"
    )
    db.commit()
    assert calc.a == 10.0
    assert calc.b == 5.0
    assert calc.type == "add"
    assert calc.result == 15.0
    assert calc.user_id == test_user.id

def test_calculation_model_subtract(db, test_user):
    """Test creating a calculation with 'subtract' type."""
    calc = Calculation.create_calculation(
        db=db,
        user_id=test_user.id,
        a=10.0,
        b=5.0,
        calc_type="subtract"
    )
    db.commit()
    assert calc.result == 5.0

def test_calculation_model_multiply(db, test_user):
    """Test creating a calculation with 'multiply' type."""
    calc = Calculation.create_calculation(
        db=db,
        user_id=test_user.id,
        a=10.0,
        b=5.0,
        calc_type="multiply"
    )
    db.commit()
    assert calc.result == 50.0

def test_calculation_model_divide(db, test_user):
    """Test creating a calculation with 'divide' type."""
    calc = Calculation.create_calculation(
        db=db,
        user_id=test_user.id,
        a=10.0,
        b=5.0,
        calc_type="divide"
    )
    db.commit()
    assert calc.result == 2.0

def test_calculation_model_divide_by_zero(db, test_user):
    """Test creating a calculation with b=0 for 'divide' type."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        Calculation.create_calculation(
            db=db,
            user_id=test_user.id,
            a=10.0,
            b=0.0,
            calc_type="divide"
        )

def test_calculation_model_invalid_user_id(db):
    """Test creating a calculation with invalid user_id."""
    with pytest.raises(ValueError, match="Invalid user_id"):
        Calculation.create_calculation(
            db=db,
            user_id=uuid4(),  # Non-existent user
            a=10.0,
            b=5.0,
            calc_type="add"
        )

def test_calculation_model_invalid_type(db, test_user):
    """Test creating a calculation with invalid type."""
    with pytest.raises(ValueError, match="Invalid calculation type: invalid"):
        Calculation.create_calculation(
            db=db,
            user_id=test_user.id,
            a=10.0,
            b=5.0,
            calc_type="invalid"
        )
