const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Patient = require('./Patient');

const Medication = sequelize.define('Medication', {
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
  name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  dosage: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  frequency: {
    type: DataTypes.STRING,
  },
  prescriber: {
    type: DataTypes.STRING,
  },
  status: {
    type: DataTypes.ENUM('active', 'discontinued', 'completed'),
    defaultValue: 'active',
  },
  started_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
}, {
  tableName: 'medications',
  timestamps: true,
});

Patient.hasMany(Medication, { foreignKey: 'patient_id' });
Medication.belongsTo(Patient, { foreignKey: 'patient_id' });

module.exports = Medication;
