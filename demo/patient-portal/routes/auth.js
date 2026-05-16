const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const User = require('../models/User');
const AuditLog = require('../models/AuditLog');

const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET || 'dev-only-jwt-secret-change-me';

router.post('/login', async (req, res) => {
  const { username, password } = req.body || {};

  if (!username || !password) {
    return res.status(400).json({ error: 'username and password required' });
  }

  // 45 CFR § 164.312(d) - Person or Entity Authentication
  // Removed hardcoded credentials - all authentication must use secure credential storage
  const user = await User.findOne({ where: { username } });
  if (!user) return res.status(401).json({ error: 'invalid credentials' });

  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'invalid credentials' });

  await AuditLog.create({
    actor_user_id: user.id,
    action: 'login',
    resource_type: 'User',
    resource_id: String(user.id),
    ip_address: req.ip,
  });

  const token = jwt.sign({ sub: user.id, role: user.role }, JWT_SECRET, { expiresIn: '24h' });
  req.session.userId = user.id;
  req.session.role = user.role;
  res.json({ token, role: user.role });
});

router.post('/logout', (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

function requireAuth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token && !req.session?.userId) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  if (token) {
    try {
      req.user = jwt.verify(token, JWT_SECRET);
    } catch {
      return res.status(401).json({ error: 'invalid token' });
    }
  } else {
    req.user = { sub: req.session.userId, role: req.session.role };
  }
  next();
}

router.requireAuth = requireAuth;
module.exports = router;
module.exports.requireAuth = requireAuth;
