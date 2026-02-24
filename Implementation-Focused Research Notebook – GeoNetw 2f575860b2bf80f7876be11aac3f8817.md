# Implementation-Focused Research Notebook – GeoNetworking & V2X Security

## Purpose of This Notebook

This notebook documents **the research findings that directly informed the practical implementation** of the internship project: *Detection of Position Spoofing Attacks in ETSI GeoNetworking using FlexStack*. The goal is to justify design choices made during implementation and to show how theoretical security concepts translate into concrete protocol-level mechanisms.

---

## 1. Security Assumptions Relevant to GeoNetworking Implementation

ETSI ITS-G5 and IEEE 802.11p-based systems rely on decentralized, broadcast-oriented communication. While cryptographic mechanisms defined in IEEE 1609.2 provide **authentication, integrity, and optional confidentiality**, they do not guarantee the correctness of the transmitted data.

**Implementation-relevant observation:**

- A node can transmit *cryptographically valid but semantically false* information (e.g., incorrect position data).
- GeoNetworking and facilities-layer services (CAM/DENM) implicitly trust GNSS-derived position information.

[GeoNetworking packet sniffing report](GeoNetworking%20packet%20sniffing%20report%202fe75860b2bf804997e6ffdd12d2beb6.md)

---

## 2. Position Trust and GNSS-Related Attacks

### 2.1 Position Spoofing as a Practical Attack

Position spoofing consists of advertising false geographic coordinates while participating normally in V2X communication. This can be achieved by:

- Manipulating GNSS inputs
- Injecting forged position values at the application or networking layer

**Why this matters for GeoNetworking:**

- Neighbor tables rely on received position updates
- Geographic routing decisions depend on relative distance
- Facilities-layer messages (CAMs, DENMs) embed position information

**Implementation insight:**

The attack does not require breaking cryptography; it exploits trust assumptions.

---

## 3. IEEE 1609.2 – What It Solves and What It Does Not

IEEE 1609.2 defines secure message formats and cryptographic services, including:

- Digital signatures for message authentication
- Certificates and pseudonyms for trust establishment
- Timestamps and sequence numbers for replay protection

**Implementation-relevant limitation:**

- IEEE 1609.2 does not validate *plausibility* of message content
- Signed CAMs or DENMs may still contain false position data

[Threat Modeling and Attack Selection](Threat%20Modeling%20and%20Attack%20Selection%2030475860b2bf80138314dba276a127cf.md)

---

## 4. Misbehavior Detection as an Implementation Strategy

Because cryptographic protection cannot prevent insider attacks, literature proposes **misbehavior detection systems** based on local observation.

### 4.1 Plausibility Checks

Plausibility-based detection evaluates whether received data is physically reasonable, for example:

- Speed derived from position change over time
- Sudden, unrealistic jumps in location
- Inconsistent movement patterns

**Implementation relevance:**

- Can be implemented locally without backend infrastructure
- Does not require access to long-term identities
- Preserves pseudonym-based privacy

---

## 5. Privacy Constraints Affecting Detection Logic

V2X systems aim to preserve privacy through pseudonym usage and identifier rotation. Detection mechanisms must therefore:

- Avoid reliance on long-term identifiers
- Operate on short-lived observations
- Tolerate identifier changes

**Implementation consequence:**

The detection logic focuses on *temporal consistency per pseudonym* rather than persistent identity tracking.

---

## 6. Facilities-Layer Services and Security Impact

### 6.1 Cooperative Awareness Messages (CAMs)

CAMs periodically broadcast position and movement data. False CAMs can corrupt neighbor tables and affect GeoNetworking behavior.

### 6.2 Decentralized Environmental Notification Messages (DENMs)

DENMs broadcast event-driven hazard warnings such as accidents, emergency vehicles, or dangerous road conditions.

**Security relevance:**

- False DENMs could cause unnecessary braking, rerouting, or panic
- Position spoofing can amplify the perceived relevance of malicious DENMs

---

## 7. Why FlexStack Is Suitable for This Implementation

FlexStack provides:

- Modular GeoNetworking components
- Facilities-layer services (CAM, DEN)
- Clear integration points for packet reception and neighbor table updates

*FlexStack allows security checks to be added without modifying cryptographic mechanisms, making it ideal for experimenting with plausibility-based detection.*

---

## Conclusion

The research confirms that while existing V2X standards provide strong cryptographic protection, they do not prevent insider attacks exploiting trusted position information. Plausibility-based detection mechanisms are therefore a practical and privacy-preserving solution that can be implemented at the GeoNetworking level. These insights directly informed the internship’s practical work using FlexStack.