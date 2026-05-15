const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Patient = require('./Patient');

const Appointment = sequelize.define('Appointment', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  patient_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: { model: Patient, key: 'id' },
  },
  provider: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  scheduled_for: {
    type: DataTypes.DATE,
    allowNull: false,
  },
  reason: {
    type: DataTypes.TEXT,
  },
  status: {
    type: DataTypes.ENUM('scheduled', 'completed', 'cancelled', 'no_show'),
    defaultValue: 'scheduled',
  },
}, {
  tableName: 'appointments',
  timestamps: true,
});

Patient.hasMany(Appointment, { foreignKey: 'patient_id' });
Appointment.belongsTo(Patient, { foreignKey: 'patient_id' });

module.exports = Appointment;
