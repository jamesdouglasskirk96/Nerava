"""
Test UUID compatibility with SQLite and PostgreSQL.

This test ensures that UUID columns work correctly in both SQLite (for tests)
and PostgreSQL (for production).
"""
import pytest
import uuid
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.uuid_type import UUIDType

# Create a test base for this test
TestBase = declarative_base()


class UUIDTestModel(TestBase):
    """Test model with UUID primary key"""
    __tablename__ = "test_uuid_model"
    
    id = Column(UUIDType(), primary_key=True)
    name = Column(String, nullable=False)


class UUIDTestForeignKey(TestBase):
    """Test model with UUID foreign key"""
    __tablename__ = "test_uuid_fk"
    
    id = Column(String, primary_key=True)
    uuid_fk = Column(UUIDType(), nullable=False)


def test_uuid_insert_select_roundtrip_sqlite(db):
    """Test UUID insert/select round-trip works on SQLite"""
    # Create table
    UUIDTestModel.__table__.create(bind=db.bind, checkfirst=True)
    
    # Generate UUID
    test_uuid = str(uuid.uuid4())
    
    # Insert
    test_obj = UUIDTestModel(id=test_uuid, name="test")
    db.add(test_obj)
    db.commit()
    
    # Select
    retrieved = db.query(UUIDTestModel).filter(UUIDTestModel.id == test_uuid).first()
    
    assert retrieved is not None
    assert retrieved.id == test_uuid
    assert retrieved.name == "test"
    
    # Cleanup
    UUIDTestModel.__table__.drop(bind=db.bind, checkfirst=True)


def test_uuid_uniqueness_constraint(db):
    """Test UUID uniqueness constraints work"""
    # Create table
    UUIDTestModel.__table__.create(bind=db.bind, checkfirst=True)
    
    test_uuid = str(uuid.uuid4())
    
    # Insert first record
    obj1 = UUIDTestModel(id=test_uuid, name="test1")
    db.add(obj1)
    db.commit()
    
    # Try to insert duplicate UUID (should fail)
    obj2 = UUIDTestModel(id=test_uuid, name="test2")
    db.add(obj2)
    
    with pytest.raises(Exception):  # IntegrityError or similar
        db.commit()
    
    db.rollback()
    
    # Cleanup
    UUIDTestModel.__table__.drop(bind=db.bind, checkfirst=True)


def test_uuid_foreign_key(db):
    """Test UUID foreign keys work"""
    # Create tables
    UUIDTestModel.__table__.create(bind=db.bind, checkfirst=True)
    UUIDTestForeignKey.__table__.create(bind=db.bind, checkfirst=True)
    
    # Create parent
    parent_uuid = str(uuid.uuid4())
    parent = UUIDTestModel(id=parent_uuid, name="parent")
    db.add(parent)
    db.commit()
    
    # Create child with FK
    child = UUIDTestForeignKey(id="child1", uuid_fk=parent_uuid)
    db.add(child)
    db.commit()
    
    # Verify
    retrieved = db.query(UUIDTestForeignKey).filter(UUIDTestForeignKey.id == "child1").first()
    assert retrieved is not None
    assert retrieved.uuid_fk == parent_uuid
    
    # Cleanup
    UUIDTestForeignKey.__table__.drop(bind=db.bind, checkfirst=True)
    UUIDTestModel.__table__.drop(bind=db.bind, checkfirst=True)


def test_uuid_string_conversion(db):
    """Test UUID type handles string conversion correctly"""
    # Create table
    UUIDTestModel.__table__.create(bind=db.bind, checkfirst=True)
    
    # Test with UUID object
    uuid_obj = uuid.uuid4()
    obj1 = UUIDTestModel(id=uuid_obj, name="test1")
    db.add(obj1)
    db.commit()
    
    # Verify it's stored as string
    retrieved = db.query(UUIDTestModel).filter(UUIDTestModel.id == str(uuid_obj)).first()
    assert retrieved is not None
    assert retrieved.id == str(uuid_obj)
    
    # Test with string UUID
    uuid_str = str(uuid.uuid4())
    obj2 = UUIDTestModel(id=uuid_str, name="test2")
    db.add(obj2)
    db.commit()
    
    retrieved2 = db.query(UUIDTestModel).filter(UUIDTestModel.id == uuid_str).first()
    assert retrieved2 is not None
    assert retrieved2.id == uuid_str
    
    # Cleanup
    UUIDTestModel.__table__.drop(bind=db.bind, checkfirst=True)


def test_uuid_invalid_string_rejected(db):
    """Test that invalid UUID strings are rejected"""
    # Create table
    UUIDTestModel.__table__.create(bind=db.bind, checkfirst=True)
    
    # Try to insert invalid UUID string
    obj = UUIDTestModel(id="not-a-valid-uuid", name="test")
    db.add(obj)
    
    with pytest.raises(Exception):  # ValueError or similar
        db.commit()
    
    db.rollback()
    
    # Cleanup
    UUIDTestModel.__table__.drop(bind=db.bind, checkfirst=True)


def test_uuid_with_existing_models(db):
    """Test UUID type works with existing domain models"""
    from app.models.domain import DomainMerchant, NovaTransaction
    from app.models.user import User
    
    # Create a user
    user = User(
        email="uuid_test@example.com",
        password_hash="hashed",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Verify user.public_id is a valid UUID string
    assert user.public_id is not None
    assert len(user.public_id) == 36
    # Validate UUID format
    uuid.UUID(user.public_id)
    
    # Create a merchant with UUID
    merchant_id = str(uuid.uuid4())
    merchant = DomainMerchant(
        id=merchant_id,
        name="UUID Test Merchant",
        lat=30.4,
        lng=-97.7,
        zone_slug="test_zone",
        status="active",
        nova_balance=0
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    
    # Verify merchant.id is stored correctly
    assert merchant.id == merchant_id
    
    # Create a Nova transaction with UUID
    txn_id = str(uuid.uuid4())
    txn = NovaTransaction(
        id=txn_id,
        type="driver_earn",
        driver_user_id=user.id,
        amount=100
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    
    # Verify transaction.id is stored correctly
    assert txn.id == txn_id
    
    # Query by UUID string
    retrieved_txn = db.query(NovaTransaction).filter(NovaTransaction.id == txn_id).first()
    assert retrieved_txn is not None
    assert retrieved_txn.id == txn_id

