require('dotenv').config();

const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');

const sessionMiddleware = require('./middleware/session');
const { sequelize } = require('./config/database');

const authRoutes = require('./routes/auth');
const patientRoutes = require('./routes/patients');
const appointmentRoutes = require('./routes/appointments');
const medicationRoutes = require('./routes/medications');
const adminRoutes = require('./routes/admin');

const app = express();

app.use(bodyParser.json({ limit: '1mb' }));
app.use(cookieParser());
app.use(sessionMiddleware);

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.use('/auth', authRoutes);
app.use('/patients', patientRoutes);
app.use('/appointments', appointmentRoutes);
app.use('/medications', medicationRoutes);
app.use('/admin', adminRoutes);

app.use((err, req, res, _next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || 'Internal Server Error' });
});

const PORT = process.env.PATIENT_PORTAL_PORT || 3000;

async function start() {
  try {
    await sequelize.authenticate();
    await sequelize.sync();
    app.listen(PORT, () => {
      console.log(`[patient-portal] listening on :${PORT}`);
    });
  } catch (e) {
    console.error('[patient-portal] failed to start', e);
    process.exit(1);
  }
}

start();
