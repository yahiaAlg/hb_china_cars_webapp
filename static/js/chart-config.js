// Chart.js Configuration and Utilities for Car Trading Application

// Default Chart Colors
const CHART_COLORS = {
    primary: '#1e3a5f',
    secondary: '#dc2626', 
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
    light: '#f8f9fa',
    dark: '#212529',
    
    // Additional color palette
    blue: '#3b82f6',
    indigo: '#6366f1',
    purple: '#8b5cf6',
    pink: '#ec4899',
    red: '#ef4444',
    orange: '#f97316',
    yellow: '#eab308',
    green: '#22c55e',
    emerald: '#10b981',
    teal: '#14b8a6',
    cyan: '#06b6d4',
    slate: '#64748b',
    gray: '#6b7280',
    zinc: '#71717a',
    neutral: '#737373',
    stone: '#78716c'
};

// Chart.js Global Configuration
Chart.defaults.font.family = 'Montserrat, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
Chart.defaults.font.size = 13;
Chart.defaults.color = '#6b7280';
Chart.defaults.borderColor = '#e5e7eb';
Chart.defaults.backgroundColor = '#f9fafb';

// Global plugin settings
Chart.defaults.plugins.legend.position = 'bottom';
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 20;
Chart.defaults.plugins.legend.labels.boxWidth = 12;

// Tooltip settings
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
Chart.defaults.plugins.tooltip.bodyColor = '#ffffff';
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;

// Chart Utilities
class ChartUtils {
    
    // Generate chart data with proper colors
    static generateDataset(label, data, type = 'line', colorKey = 'primary') {
        const color = CHART_COLORS[colorKey] || CHART_COLORS.primary;
        
        const baseDataset = {
            label: label,
            data: data,
            borderColor: color,
            backgroundColor: this.hexToRgba(color, 0.1),
            borderWidth: 2,
            pointBackgroundColor: color,
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        };

        if (type === 'bar') {
            return {
                ...baseDataset,
                backgroundColor: this.hexToRgba(color, 0.8),
                borderWidth: 0
            };
        }

        if (type === 'doughnut' || type === 'pie') {
            return {
                ...baseDataset,
                backgroundColor: [
                    CHART_COLORS.primary,
                    CHART_COLORS.success,
                    CHART_COLORS.warning,
                    CHART_COLORS.danger,
                    CHART_COLORS.info,
                    CHART_COLORS.secondary
                ],
                borderWidth: 0
            };
        }

        if (type === 'area') {
            return {
                ...baseDataset,
                fill: true,
                backgroundColor: this.hexToRgba(color, 0.2),
                tension: 0.4
            };
        }

        return baseDataset;
    }

    // Convert hex to rgba
    static hexToRgba(hex, opacity) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }

    // Common chart options
    static getCommonOptions(type = 'line') {
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            elements: {
                point: {
                    radius: 4,
                    hoverRadius: 6,
                    borderWidth: 2
                },
                line: {
                    tension: 0.4,
                    borderWidth: 2
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleFont: {
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 12
                    },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true
                }
            }
        };

        if (type === 'line' || type === 'bar') {
            baseOptions.scales = {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f3f4f6'
                    },
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                }
            };
        }

        return baseOptions;
    }

    // Currency formatter for tooltips
    static currencyFormatter(value, context) {
        return new Intl.NumberFormat('fr-DZ', {
            style: 'currency',
            currency: 'DZD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    // Number formatter
    static numberFormatter(value) {
        return new Intl.NumberFormat('fr-DZ').format(value);
    }

    // Percentage formatter
    static percentageFormatter(value) {
        return value.toFixed(1) + '%';
    }

    // Create sales trend chart
    static createSalesTrendChart(ctx, data) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    this.generateDataset('Ventes (DA)', data.sales, 'area', 'primary'),
                    this.generateDataset('Objectif (DA)', data.target, 'line', 'secondary')
                ]
            },
            options: {
                ...this.getCommonOptions('line'),
                plugins: {
                    ...this.getCommonOptions('line').plugins,
                    tooltip: {
                        ...this.getCommonOptions('line').plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + ChartUtils.currencyFormatter(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    ...this.getCommonOptions('line').scales,
                    y: {
                        ...this.getCommonOptions('line').scales.y,
                        ticks: {
                            callback: function(value) {
                                return ChartUtils.currencyFormatter(value);
                            },
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }

    // Create inventory status chart
    static createInventoryStatusChart(ctx, data) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [this.generateDataset('Véhicules', data.values, 'doughnut')]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // We'll show custom legend
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} véhicules (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Create commission chart
    static createCommissionChart(ctx, data) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.traders,
                datasets: [
                    this.generateDataset('Commissions (DA)', data.commissions, 'bar', 'success'),
                    this.generateDataset('Ventes', data.sales, 'bar', 'info')
                ]
            },
            options: {
                ...this.getCommonOptions('bar'),
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        position: 'left',
                        grid: { color: '#f3f4f6' },
                        ticks: {
                            callback: function(value) {
                                return ChartUtils.currencyFormatter(value);
                            },
                            font: { size: 11 }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        grid: { drawOnChartArea: false },
                        ticks: {
                            callback: function(value) {
                                return value + ' ventes';
                            },
                            font: { size: 11 }
                        }
                    }
                },
                plugins: {
                    ...this.getCommonOptions('bar').plugins,
                    tooltip: {
                        ...this.getCommonOptions('bar').plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    return 'Commissions: ' + ChartUtils.currencyFormatter(context.parsed.y);
                                } else {
                                    return 'Ventes: ' + context.parsed.y;
                                }
                            }
                        }
                    }
                }
            }
        });
    }

    // Create profit analysis chart
    static createProfitChart(ctx, data) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    this.generateDataset('Chiffre d\'Affaires', data.revenue, 'bar', 'primary'),
                    this.generateDataset('Coûts', data.costs, 'bar', 'danger'),
                    this.generateDataset('Marge', data.profit, 'bar', 'success')
                ]
            },
            options: {
                ...this.getCommonOptions('bar'),
                plugins: {
                    ...this.getCommonOptions('bar').plugins,
                    tooltip: {
                        ...this.getCommonOptions('bar').plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + ChartUtils.currencyFormatter(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    ...this.getCommonOptions('bar').scales,
                    y: {
                        ...this.getCommonOptions('bar').scales.y,
                        ticks: {
                            callback: function(value) {
                                return ChartUtils.currencyFormatter(value);
                            },
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }

    // Animate chart on load
    static animateChart(chart) {
        chart.update('show');
    }

    // Update chart data
    static updateChartData(chart, newData) {
        chart.data = newData;
        chart.update('show');
    }

    // Destroy chart safely
    static destroyChart(chart) {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    }
}

// Make utilities available globally
window.ChartUtils = ChartUtils;
window.CHART_COLORS = CHART_COLORS;

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChartUtils, CHART_COLORS };
}