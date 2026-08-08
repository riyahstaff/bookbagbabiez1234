from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProjectSetting, ProviderConfiguration
from app.schemas.settings import (
    ProjectSettingRead,
    ProjectSettingUpsert,
    ProviderConfigurationCreate,
    ProviderConfigurationRead,
    ProviderConfigurationUpdate,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/project", response_model=list[ProjectSettingRead])
def list_project_settings(db: Session = Depends(get_db)):
    return db.query(ProjectSetting).order_by(ProjectSetting.key).all()


@router.put("/project", response_model=ProjectSettingRead)
def upsert_project_setting(payload: ProjectSettingUpsert, db: Session = Depends(get_db)):
    setting = db.query(ProjectSetting).filter(ProjectSetting.key == payload.key).first()
    if setting:
        setting.value = payload.value
    else:
        setting = ProjectSetting(key=payload.key, value=payload.value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.get("/providers", response_model=list[ProviderConfigurationRead])
def list_provider_configurations(db: Session = Depends(get_db)):
    return db.query(ProviderConfiguration).order_by(ProviderConfiguration.capability).all()


@router.post("/providers", response_model=ProviderConfigurationRead, status_code=201)
def create_provider_configuration(
    payload: ProviderConfigurationCreate, db: Session = Depends(get_db)
):
    config = ProviderConfiguration(
        capability=payload.capability.value,
        provider_name=payload.provider_name,
        is_default=payload.is_default,
        config=payload.config,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.patch("/providers/{config_id}", response_model=ProviderConfigurationRead)
def update_provider_configuration(
    config_id: int, payload: ProviderConfigurationUpdate, db: Session = Depends(get_db)
):
    config = db.get(ProviderConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/providers/{config_id}", status_code=204)
def delete_provider_configuration(config_id: int, db: Session = Depends(get_db)):
    config = db.get(ProviderConfiguration, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration not found")
    db.delete(config)
    db.commit()
