const express = require('express');

const Patient = require('../models/Patient');
const AuditLog = require('../models/AuditLog');
const { requireAuth } = require('./auth');

const router = express.Router();

function requireAdmin(req, res, next) {
  if (req.user?.role !== 'admin') {
    return res.status(403).json({ error: 'forbidden' });
  }
  next();
}

router.get('/export', requireAuth, requireAdmin, async (req, res) => {
  const rows = await Patient.findAll({
    attributes: ['id', 'first_name', 'last_name', 'dob', 'mrn', 'diagnosis'],
  });
  await AuditLog.create({
    actor_user_id: req.user?.sub,
    action: 'export',
    resource_type: 'Patient',
    ip_address: req.ip,
    metadata: { count: rows.length },
  });
  res.json(rows);
});

router.get('/audit', requireAuth, requireAdmin, async (req, res) => {
  const rows = await AuditLog.findAll({
    order: [['occurred_at', 'DESC']],
    limit: 200,
  });
  res.json(rows);
});

module.exports = router;
