# Advanced AI Module for OFITEC.AI

## Overview

The Advanced AI Module is a comprehensive artificial intelligence solution for Odoo that provides machine learning capabilities, predictive analytics, real-time metrics, and horizontal scaling features. This module is designed to enhance decision-making processes through intelligent automation and data-driven insights.

## Features

### 🤖 Machine Learning Models
- **Cost Overrun Prediction**: Predict project cost overruns using XGBoost algorithms
- **Risk Assessment**: Evaluate project risks with Random Forest models
- **Schedule Forecasting**: Forecast project delays using LightGBM
- **Quality Prediction**: Predict quality issues and defects
- **Resource Optimization**: Optimize resource allocation
- **Anomaly Detection**: Detect unusual patterns in project data

### 📊 Predictive Analytics
- Real-time project analysis
- AI-powered recommendations
- Risk trend analysis
- Cost-benefit analysis
- Schedule optimization suggestions

### 📈 Real-time Metrics Dashboard
- Live KPI monitoring
- Performance tracking
- Quality metrics
- Risk indicators
- Custom metric creation

### 🔌 REST API
- Complete REST API for external integrations
- OAuth2 authentication
- Swagger documentation
- Rate limiting and security controls

### ⚖️ Horizontal Scaling
- Redis caching for performance
- Load balancing across multiple workers
- Auto-scaling capabilities
- System monitoring and alerting

### 🔒 Security & Compliance
- Role-based access control
- API access logging
- Data encryption
- Security audit trails
- Webhook security validation

## Installation

### Prerequisites

- Odoo 16.0 or higher
- Python 3.8+
- Redis server (for caching and scaling)
- Required Python packages:
  ```
  pip install scikit-learn xgboost lightgbm tensorflow pandas numpy matplotlib seaborn redis requests
  ```

### Installation Steps

1. **Clone or copy the module** to your Odoo addons directory:
   ```bash
   cp -r ofitec_ai_advanced /path/to/odoo/addons/
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements-ai.txt
   ```

3. **Update Odoo configuration** (optional):
   ```python
   # Add to your odoo.conf
   addons_path = /path/to/odoo/addons,/path/to/custom/addons
   ```

4. **Restart Odoo** and install the module through the web interface

5. **Run the installation script**:
   ```bash
   python install_ai_advanced.py
   ```

## Configuration

### Basic Setup

1. **Access the AI Dashboard**:
   - Navigate to `Advanced AI > AI Dashboard`
   - Configure your first ML models

2. **Set up Real-time Metrics**:
   - Go to `Advanced AI > Real-time Metrics`
   - Configure KPIs and monitoring thresholds

3. **Configure API Access**:
   - Navigate to `Advanced AI > AI Security`
   - Set up API authentication and permissions

### Advanced Configuration

#### Redis Setup
```python
# In your ai_config.py
CACHE_CONFIG = {
    'redis_host': 'your-redis-host',
    'redis_port': 6379,
    'redis_password': 'your-password',
    'ttl': 3600
}
```

#### Load Balancing
```python
SCALING_CONFIG = {
    'enable_load_balancing': True,
    'worker_nodes': [
        'http://worker1:8069',
        'http://worker2:8069',
        'http://worker3:8069'
    ],
    'load_balancing_strategy': 'least_loaded'
}
```

#### Webhook Integration
```python
WEBHOOK_CONFIG = {
    'powerbi': {
        'url': 'https://your-powerbi-webhook-url',
        'secret': 'your-webhook-secret'
    }
}
```

## Usage

### Training ML Models

1. **Access Model Management**:
   - Go to `Advanced AI > ML Models`
   - Select or create a new model

2. **Configure Model Parameters**:
   - Choose algorithm (XGBoost, LightGBM, Random Forest)
   - Set training parameters
   - Define data sources

3. **Train the Model**:
   - Click "Train Model" button
   - Monitor training progress
   - Review model performance metrics

### Using Predictive Analytics

1. **Run Project Analysis**:
   ```python
   from odoo import api, models

   class YourController(models.AbstractModel):
       @api.model
       def analyze_project(self, project_id):
           predictive = self.env['ofitec.ai.predictive']
           results = predictive.run_predictive_analysis(project_id)
           return results
   ```

2. **Get Real-time Metrics**:
   ```python
   metrics = self.env['ofitec.ai.api'].get_realtime_metrics()
   ```

### API Integration

#### Authentication
```bash
# Get API token
curl -X POST http://your-odoo/api/v1/ai/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "your-user", "password": "your-password"}'
```

#### Make Predictions
```bash
# Predict using trained model
curl -X POST http://your-odoo/api/v1/ai/predict \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "cost_prediction",
    "features": [1000, 5, 1, 30]
  }'
```

#### Get Analytics
```bash
# Get predictive insights
curl -X GET http://your-odoo/api/v1/ai/analytics/predictive \
  -H "Authorization: Bearer your-token"
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/models` | List available models |
| POST | `/api/v1/ai/models/{id}/train` | Train specific model |
| POST | `/api/v1/ai/predict` | Make prediction |
| GET | `/api/v1/ai/analytics/realtime` | Get real-time metrics |
| GET | `/api/v1/ai/analytics/predictive` | Get predictive analytics |
| POST | `/api/v1/ai/webhook/{service}` | Webhook endpoints |

### Response Format
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Security

### Access Control
- **AI User**: Basic access to AI features
- **AI Manager**: Model management and configuration
- **AI Admin**: Full system access and security settings

### Data Protection
- All sensitive data is encrypted at rest
- API requests are logged for audit purposes
- Rate limiting prevents abuse
- Webhook signatures are validated

### Best Practices
1. Regularly update ML models
2. Monitor system performance
3. Implement proper backup strategies
4. Use HTTPS in production
5. Regularly review access logs

## Monitoring & Maintenance

### Health Checks
```python
# Check system health
scaling = env['ofitec.ai.scaling'].search([], limit=1)
health = scaling.perform_health_check()
```

### Performance Monitoring
```python
# Get performance metrics
metrics = scaling.get_performance_metrics()
```

### Log Analysis
```python
# Review access logs
logs = env['ofitec.ai.access_log'].search([
    ('access_time', '>=', '2024-01-01')
])
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis server status
   - Verify connection parameters
   - Ensure Redis is accessible from Odoo

2. **Model Training Failed**
   - Check data availability
   - Verify model parameters
   - Review error logs

3. **API Authentication Failed**
   - Verify token validity
   - Check user permissions
   - Review security settings

### Debug Mode
Enable debug logging by setting:
```python
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'file': '/var/log/odoo/ai_advanced_debug.log'
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This module is licensed under the Odoo Proprietary License. See LICENSE file for details.

## Support

For support and questions:
- Email: support@ofitec.ai
- Documentation: https://docs.ofitec.ai
- Issues: https://github.com/ofitec/ai-advanced/issues

## Changelog

### Version 1.0.0
- Initial release
- ML model implementations
- Predictive analytics
- Real-time metrics
- REST API
- Security features
- Horizontal scaling support
