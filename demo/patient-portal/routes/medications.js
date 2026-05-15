const express = require('express');
const axios = require('axios');

const Medication = require('../models/Medication');
const { requireAuth } = require('./auth');

const router = express.Router();

const PHARMACY_API = process.env.PHARMACY_API
  || 'http://internal-pharmacy-api/v1/prescriptions';

router.get('/:patientId', requireAuth, async (req, res) => {
  const rows = await Medication.findAll({
    where: { patient_id: req.params.patientId },
    order: [['started_at', 'DESC']],
  });
  res.json(rows);
});

router.post('/', requireAuth, async (req, res) => {
  const med = await Medication.create({
    patient_id: req.body.patient_id,
    name: req.body.name,
    dosage: req.body.dosage,
    frequency: req.body.frequency,
    prescriber: req.body.prescriber,
  });

  try {
    await axios.post(PHARMACY_API, {
      patient_id: med.patient_id,
      drug: med.name,
      dose: med.dosage,
      schedule: med.frequency,
    });
  } catch (e) {
    console.warn('[medications] pharmacy push failed', e.message);
  }

  res.status(201).json(med);
});

router.get('/lookup/:rxcui', requireAuth, async (req, res) => {
  const resp = await axios.get(`${PHARMACY_API}/lookup/${req.params.rxcui}`);
  res.json(resp.data);
});

router.post('/discontinue', requireAuth, async (req, res) => {
  const { patient_id, status } = req.body;
  const [count] = await Medication.update(
    { status },
    { where: { patient_id } }
  );
  res.json({ updated: count });
});

module.exports = router;
