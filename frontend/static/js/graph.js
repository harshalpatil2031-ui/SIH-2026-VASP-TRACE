/**
 * Graph Visualization Manager using Cytoscape.js with simple, intuitive terms.
 */
let cy = null;

function initCytoscape(containerId) {
    cy = cytoscape({
        container: document.getElementById(containerId),
        boxSelectionEnabled: false,
        autounselectify: false,
        style: [
            // Base Node Style
            {
                selector: 'node',
                style: {
                    'label': 'data(simpleLabel)',
                    'color': '#f8fafc',
                    'font-family': 'Inter, sans-serif',
                    'font-size': '12px',
                    'font-weight': 700,
                    'text-valign': 'bottom',
                    'text-margin-y': 8,
                    'text-background-opacity': 0.9,
                    'text-background-color': '#090d16',
                    'text-background-padding': '4px',
                    'text-background-shape': 'roundrectangle',
                    'text-border-opacity': 0.6,
                    'text-border-width': 1,
                    'text-border-color': '#334155',
                    'width': 48,
                    'height': 48,
                    'background-color': '#475569',
                    'border-width': 2,
                    'border-color': '#64748b'
                }
            },
            // 1. Suspect Wallet (Red)
            {
                selector: 'node[type = "suspect"]',
                style: {
                    'background-color': '#dc2626',
                    'border-color': '#f87171',
                    'border-width': 3,
                    'width': 54,
                    'height': 54,
                    'shadow-blur': 15,
                    'shadow-color': '#ef4444',
                    'shadow-opacity': 0.8
                }
            },
            // 2. Mule Intermediary (Amber)
            {
                selector: 'node[type = "mule"]',
                style: {
                    'background-color': '#d97706',
                    'border-color': '#fbbf24',
                    'border-width': 2
                }
            },
            // 3. Shared Mule (Cross-Case Syndicate Match - Pulsing Red/Amber Diamond)
            {
                selector: 'node[?is_shared]',
                style: {
                    'background-color': '#b45309',
                    'border-color': '#ef4444',
                    'border-width': 4,
                    'shape': 'diamond',
                    'width': 58,
                    'height': 58,
                    'shadow-blur': 25,
                    'shadow-color': '#ef4444',
                    'shadow-opacity': 0.9
                }
            },
            // 4. Exchange Deposit Account (Purple)
            {
                selector: 'node[type = "deposit"]',
                style: {
                    'background-color': '#7c3aed',
                    'border-color': '#a78bfa',
                    'border-width': 2,
                    'shape': 'pentagon',
                    'width': 50,
                    'height': 50
                }
            },
            // 5. Crypto Exchange (Green Round Rectangle)
            {
                selector: 'node[type = "vasp_hot"]',
                style: {
                    'background-color': '#059669',
                    'border-color': '#34d399',
                    'border-width': 3,
                    'shape': 'round-rectangle',
                    'width': 60,
                    'height': 50,
                    'shadow-blur': 20,
                    'shadow-color': '#10b981',
                    'shadow-opacity': 0.9
                }
            },
            // Edges (Fund Flow Arrows)
            {
                selector: 'edge',
                style: {
                    'width': 2.5,
                    'line-color': '#06b6d4',
                    'target-arrow-color': '#06b6d4',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'line-style': 'dashed',
                    'line-dash-pattern': [6, 3],
                    'label': 'data(amountLabel)',
                    'font-family': 'Inter, sans-serif',
                    'font-size': '11px',
                    'font-weight': 700,
                    'color': '#a5f3fc',
                    'text-background-opacity': 0.9,
                    'text-background-color': '#090d16',
                    'text-background-padding': '3px',
                    'text-background-shape': 'roundrectangle',
                    'text-border-color': '#0891b2',
                    'text-border-width': 1,
                    'arrow-scale': 1.3
                }
            },
            {
                selector: 'edge[?is_sweep]',
                style: {
                    'width': 3.5,
                    'line-color': '#10b981',
                    'target-arrow-color': '#10b981',
                    'line-style': 'solid',
                    'color': '#6ee7b7',
                    'text-border-color': '#059669'
                }
            }
        ],
        layout: {
            name: 'breadthfirst',
            directed: true,
            roots: 'node[type = "suspect"]',
            padding: 50,
            spacingFactor: 1.5,
            animate: true,
            animationDuration: 500
        }
    });

    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        if (window.onNodeSelected) {
            window.onNodeSelected(node.data());
        }
    });

    cy.on('tap', function (evt) {
        if (evt.target === cy) {
            if (window.onNodeDeselected) {
                window.onNodeDeselected();
            }
        }
    });
}

function renderGraphData(nodesData, edgesData) {
    if (!cy) {
        initCytoscape("cy");
    }
    if (!cy) return;

    cy.elements().remove();

    const cyNodes = nodesData.map(n => {
        let label = n.label;
        return {
            group: 'nodes',
            data: {
                ...n,
                simpleLabel: label
            }
        };
    });

    const cyEdges = edgesData.map(e => ({
        group: 'edges',
        data: {
            ...e,
            amountLabel: `${e.amount.toLocaleString()} ${e.token}`
        }
    }));

    cy.add(cyNodes);
    cy.add(cyEdges);

    const layout = cy.layout({
        name: 'breadthfirst',
        directed: true,
        roots: 'node[type = "suspect"]',
        padding: 50,
        spacingFactor: 1.6,
        avoidOverlap: true,
        animate: true,
        animationDuration: 600
    });
    layout.run();
    cy.fit(null, 50);
}

function clearGraphCanvas() {
    if (cy) {
        cy.elements().remove();
    }
}

function resetGraphView() {
    if (cy) {
        cy.fit(null, 50);
        cy.center();
    }
}

function zoomGraph(factor) {
    if (cy) {
        cy.zoom({
            level: cy.zoom() * factor,
            renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
        });
    }
}
