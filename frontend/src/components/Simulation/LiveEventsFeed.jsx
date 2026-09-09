/**
 * AegisAI Live Events Feed Component
 * Real-time streaming log of digital twin simulation events and incidents.
 */

import React from "react";

export function LiveEventsFeed({ events = [] }) {
    const getEventIcon = (eventType) => {
        switch (eventType) {
            case "INCIDENT_SPAWNED":
                return "🚨";
            case "BUILDING_DAMAGED":
                return "🏢";
            case "ROAD_BLOCKED":
                return "🚧";
            case "ROAD_CLEARED":
                return "🛣️";
            case "CITIZEN_ENDANGERED":
                return "⚠️";
            case "CITIZEN_EVACUATING":
                return "🏃";
            case "CITIZEN_INJURED":
                return "🩹";
            case "CITIZEN_RESCUED":
                return "✨";
            case "WEATHER_CHANGED":
                return "🌪️";
            default:
                return "📡";
        }
    };

    const getEventClass = (eventType) => {
        switch (eventType) {
            case "INCIDENT_SPAWNED":
            case "CITIZEN_INJURED":
                return "event-critical";
            case "BUILDING_DAMAGED":
            case "ROAD_BLOCKED":
            case "CITIZEN_ENDANGERED":
                return "event-warning";
            case "CITIZEN_RESCUED":
            case "ROAD_CLEARED":
                return "event-success";
            default:
                return "event-info";
        }
    };

    const formatTimestamp = (ts) => {
        if (!ts) return "";
        try {
            const date = new Date(ts);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch {
            return ts;
        }
    };

    return (
        <div className="live-events-panel">
            <div className="section-title-bar">
                <div className="title-left">
                    <span>⚡</span>
                    <h3>Real-Time Event Stream</h3>
                </div>
                <span className="event-count-badge">{events.length} Events</span>
            </div>

            {events.length === 0 ? (
                <div className="no-events-box">
                    <p>No simulation events recorded yet.</p>
                    <span>Events will stream live as the Digital Twin simulation runs.</span>
                </div>
            ) : (
                <div className="events-stream-list">
                    {events.map((ev, index) => (
                        <div key={ev.id || `${ev.tick}-${index}`} className={`event-stream-card ${getEventClass(ev.event_type)}`}>
                            <div className="event-card-header">
                                <span className="event-icon">{getEventIcon(ev.event_type)}</span>
                                <span className="event-type-label">{ev.event_type?.replace(/_/g, " ")}</span>
                                <span className="event-tick-tag">Tick #{ev.tick}</span>
                                <span className="event-time">{formatTimestamp(ev.timestamp)}</span>
                            </div>
                            <div className="event-desc">{ev.description}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LiveEventsFeed;
