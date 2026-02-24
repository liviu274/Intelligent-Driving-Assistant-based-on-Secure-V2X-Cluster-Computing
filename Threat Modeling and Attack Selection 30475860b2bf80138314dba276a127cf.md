# Threat Modeling and Attack Selection

A relevant security threat, based on open-source v2x-FlexStack implementation

The attack surface lies in periodic CAM broadcasts containing self-reported mobility data such as:

- ITS-S type
- Timestamp
- Coordinates (latitude, longitude)
- speed / heading (relevant in a live cluster scenario)

All this data is found at link layer inside geonetworking extended header of a commonly transmitted CAM packet, sniffed from network traffic.

The attack above represents an authenticated insider position spoofing attack, where mobility parameter are deliberately falsified in order to falsify information inside an autonomous system.

Given the sniffed information here is a detailed explanation of our threat model:

1. System Model
    1. Nodes → ITS-S Stations
    2. Communication → Periodic CAM broadcast
    3. Trust → Nodes accept authenticated messages as valid
    4. Security mechanism → IEEE 1609.2 ensures authenticity & integrity (not yet implemeted)
2. Security Assumptions
    1. Messages are signed
    2. Certificates are valid
    3. No external position verification exists
    4. Nodes trust received authenticated data
3. Attack Model:
    1. Capabilities:
        1. Possesses valid certificate
        2. Can generate properly signed CAM messages
        3. Can modify position-related fields
        4. Can broadcast at normal frequency (1000 ms)
    2. Limitations: 
        1. Cannot break cryptographic primitives
        2. Cannot modify other nodes’ packets in transit
        3. Cannot control entire network
4. Attack Description
    
    The attacker deliberately falsifies the mobility parameters (latitude, longitude, speed, heading) within the CAM extended header while maintaining valid authentication.
    
5. Security Properties violated:
    1. Integrity of situational awareness
    2. Trustworthiness of geographic routing
    3. Reliability of neighbor tables
    4. Availability (in cluster disruption cases)
6. Goals:
    1. Creating ghost vehicles that compromise network infrastructure
    2. Routing decisions may use invalid geographic data
    3. Collision avoidance systems may react incorrectly
    4. May trigger falsifies DEN messages (false road emergencies) 

 

Although IEEE 1609.2 defines security services for vehicular communications, the evaluated open-source v2x-FlexStack implementation does not enforce cryptographic message signing and verification in the tested configuration. Therefore, CAM messages are accepted without authentication guarantees, increasing exposure to spoofing attacks.