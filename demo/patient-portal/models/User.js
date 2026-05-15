const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  username: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
  },
  password_hash: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  role: {
    type: DataTypes.ENUM('patient', 'nurse', 'doctor', 'admin'),
    defaultValue: 'patient',
  },
  email: {
    type: DataTypes.STRING,
    validate: { isEmail: true },
  },
}, {
  tableName: 'users',
  timestamps: true,
});

module.exports = User;
