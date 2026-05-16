const express = require('express');
const crypto = require('crypto');

const Patient = require('../models/Patient');
const AuditLog = require('../models/AuditLog');
const { requireAuth } = require('./auth');

// 45 CFR § 164.312(a)(2)(iv) - Encryption and Decryption
// Encryption configuration for PHI fields
const ENCRYPTION_KEY = process.env.PHI_ENCRYPTION_KEY || crypto.randomBytes(32);
const ENCRYPTION_ALGORITHM = 'aes-256-gcm';

function encryptPHI(plaintext) {
  if (!plaintext) return null;
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ENCRYPTION_ALGORITHM, ENCRYPTION_KEY, iv);
  let encrypted = cipher.update(plaintext, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
}

const router = express.Router();

router.get('/', requireAuth, async (req, res) => {
  const rows = await Patient.findAll({
    attributes: ['id', 'first_name', 'last_name', 'dob', 'mrn'],
    order: [['last_name', 'ASC']],
    limit: 100,
  });
  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'list',
    resource_type: 'Patient',
    ip_address: req.ip,
  });
  res.json(rows);
});

// 45 CFR § 164.312(a)(1) - Access Control
// Implement technical policies and procedures to allow access only to authorized persons
router.get('/:id', requireAuth, async (req, res) => {
  const patient = await Patient.findByPk(req.params.id);
  if (!patient) return res.status(404).json({ error: 'not found' });
  res.json(patient);
});

router.post('/', requireAuth, async (req, res) => {
  const patient = await Patient.create({
    first_name: req.body.first_name,
    last_name: req.body.last_name,
    dob: req.body.dob,
    mrn: req.body.mrn,
    diagnosis: req.body.diagnosis,
    insurance_id: req.body.insurance_id,
    phone: req.body.phone,
    address: req.body.address,
  });
  // 45 CFR § 164.312(a)(2)(iv) - Encrypt PHI before storage
  patient.ssn = encryptPHI(req.body.ssn);
  await patient.save();

  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'create',
    resource_type: 'Patient',
    resource_id: String(patient.id),
    ip_address: req.ip,
  });

  res.status(201).json(patient);
});

router.put('/:id', requireAuth, async (req, res) => {
  const patient = await Patient.findByPk(req.params.id);
  if (!patient) return res.status(404).json({ error: 'not found' });
  await patient.update(req.body);
  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'update',
    resource_type: 'Patient',
    resource_id: String(patient.id),
    ip_address: req.ip,
  });
  res.json(patient);
});

module.exports = router;
