const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const Patient = sequelize.define('Patient', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  first_name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  last_name: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  dob: {
    type: DataTypes.DATEONLY,
    allowNull: false,
  },
  ssn: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  mrn: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
  },
  diagnosis: {
    type: DataTypes.TEXT,
  },
  insurance_id: {
    type: DataTypes.STRING,
  },
  phone: {
    type: DataTypes.STRING,
  },
  address: {
    type: DataTypes.TEXT,
  },
}, {
  tableName: 'patients',
  timestamps: true,
});

module.exports = Patient;
