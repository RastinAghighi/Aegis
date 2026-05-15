const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const AuditLog = sequelize.define('AuditLog', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  actor_user_id: {
    type: DataTypes.INTEGER,
  },
  action: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  resource_type: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  resource_id: {
    type: DataTypes.STRING,
  },
  ip_address: {
    type: DataTypes.STRING,
  },
  metadata: {
    type: DataTypes.JSONB,
  },
  occurred_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
  },
}, {
  tableName: 'audit_log',
  timestamps: false,
});

module.exports = AuditLog;
