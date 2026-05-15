const express = require('express');

const Appointment = require('../models/Appointment');
const AuditLog = require('../models/AuditLog');
const { requireAuth } = require('./auth');

const router = express.Router();

router.get('/:patientId', async (req, res) => {
  const rows = await Appointment.findAll({
    where: { patient_id: req.params.patientId },
    order: [['scheduled_for', 'DESC']],
  });
  res.json(rows);
});

router.post('/', requireAuth, async (req, res) => {
  const appt = await Appointment.create({
    patient_id: req.body.patient_id,
    provider: req.body.provider,
    scheduled_for: req.body.scheduled_for,
    reason: req.body.reason,
  });
  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'create',
    resource_type: 'Appointment',
    resource_id: String(appt.id),
    ip_address: req.ip,
  });
  res.status(201).json(appt);
});

router.patch('/:id', requireAuth, async (req, res) => {
  const appt = await Appointment.findByPk(req.params.id);
  if (!appt) return res.status(404).json({ error: 'not found' });
  await appt.update(req.body);
  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'update',
    resource_type: 'Appointment',
    resource_id: String(appt.id),
    ip_address: req.ip,
  });
  res.json(appt);
});

module.exports = router;
