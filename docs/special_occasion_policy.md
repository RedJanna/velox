# Special Occasion Policy

This document defines the standardized policy and backend decision logic for hotel special occasion requests. It is designed for guest-facing WhatsApp automation, admin approval workflows, CRM continuity, and safe operational handoff.

Core rule: the system must never finalize, guarantee, price, or operationally approve any special occasion request by itself. Every special occasion request is subject to availability and live representative/admin approval.

## Supported special occasion types

The following occasion types are supported for automated intake:

| Type | Automated behavior | Final decision |
|---|---|---|
| Birthday | Collect required information, explain only allowed policy-level distinctions, notify admin/representative for approval. | Live representative/admin only |
| Honeymoon | Collect required information, explain standard complimentary preparation scope, notify admin/representative for approval. | Live representative/admin only |
| Anniversary | Collect required information, explain allowed policy-level distinctions, notify admin/representative for approval. | Live representative/admin only |
| Marriage proposal | Collect required information, do not finalize, transfer to live representative/admin after intake. | Live representative/admin only |

For these types, the system may collect the required fields and use short, warm messages. It must not confirm that the preparation will be done until the representative/admin approves it.

## Unsupported or human-handoff-required special occasion types

The following request types require live representative/admin handling. The system must not provide pricing, confirmation, availability guarantees, or operational approval.

| Request type | Required automated behavior |
|---|---|
| Engagement | Collect available context, create handoff/admin notification. |
| Graduation | Collect available context, create handoff/admin notification. |
| Wedding | Collect available context, create handoff/admin notification. |
| Any other special occasion type | Collect available context, create handoff/admin notification. |
| Corporate celebration | Collect available context, create handoff/admin notification. |
| Business dinner | Collect available context, create handoff/admin notification. |
| Promotion celebration | Collect available context, create handoff/admin notification. |
| Team organization | Collect available context, create handoff/admin notification. |
| Children's birthday | Collect available context, create handoff/admin notification. |
| Child-specific celebrations | Collect available context, create handoff/admin notification. |
| Group celebrations | Collect available context, create handoff/admin notification. |

If the guest provides enough context in the first message, the system should create the handoff immediately. If important fields are missing, the system may ask one compact intake message before handoff only when this does not delay a safety, payment, complaint, or uncertainty escalation. If a terminal handoff ticket is already created, the AI must not continue asking questions.

## Service scope

Supported preparation categories:

- Room decoration
- Restaurant table decoration
- Cake
- Flowers
- Special table arrangement
- Fruit plate
- Wine offering
- Note card
- Music
- Photo/video support
- Gift preparation
- Personalized concept design

The service scope must be evaluated by content, date, availability, supplier needs, operational feasibility, hotel standards, and representative/admin approval.

The hotel may:

- Provide full organization support.
- Provide partial organization support.
- Arrange external suppliers.
- Allow the guest to bring their own decoration materials.
- Shop on behalf of the guest.
- Reject requests that do not match hotel visual standards, safety rules, or appropriateness rules.

The system must not promise any of these actions. It can only collect details and forward the request for approval.

## Free/paid service distinction

The system may describe only the distinction between complimentary and paid categories. It must never share prices, price ranges, fixed fees, supplier prices, deposit amounts, payment links, or cancellation fees.

### Complimentary categories

The following categories may be complimentary, subject to availability and representative/admin approval:

| Occasion type | Complimentary categories |
|---|---|
| Birthday | Restaurant table decoration, room decoration, standard wine and fruit offering |
| Honeymoon | Room decoration, fruit plate, standard wine offering |
| Anniversary | Room decoration, fruit plate, standard wine offering, restaurant table decoration |

### Paid categories

The following categories may be paid and require live representative/admin handling:

- Cake
- Flowers
- Photo/video
- Gift
- Champagne or special beverages
- Special materials other than a simple note card
- Engagement, wedding, graduation, and special organization requests
- Any additional service requiring an external supplier

### Package and pricing policy

- The hotel does not offer ready-made special occasion packages.
- Customer-facing meaning: "We do not have ready-made packages; requests are evaluated based on content and availability."
- Prices are not fixed and vary depending on request content, supplier needs, and operational feasibility.
- Only a live representative/admin may provide pricing, payment, prepayment, deposit, payment method, or cancellation information.
- If the guest asks about price, prepayment, deposit, payment method, or cancellation policy, the system must collect only safe required occasion information if not already collected, then transfer the matter to a live representative/admin.
- The system must never request credit card, CVV, OTP, bank password, identity document, or other sensitive data.

## Reservation and information collection rules

A reservation is required for every special occasion request.

Required information:

| Field | Required | Notes |
|---|---:|---|
| Full name | Yes | Use only for request handling; do not log raw name in technical logs. |
| Phone number | Yes | Store/log masked or hashed according to privacy rules. |
| Reservation number | Yes, when available | Accommodation or restaurant reservation reference. |
| Reservation type | Yes | `accommodation`, `restaurant`, or `unknown`. |
| Special occasion type | Yes | Normalize to supported or handoff-required type. |
| Special occasion date | Yes | Must be validated as a calendar date. |
| Number of people | Yes | Required for restaurant, table setup, cake, group handling. |
| Request details | Yes | Decoration/service/content details. |
| Additional requests | Yes | Can be `none` if guest has no extra request. |
| Surprise information | Yes | Whether it is a surprise and for whom. |
| Allergy or food sensitivity | Yes | Required for cake, food, beverage, fruit, restaurant setup. |
| Room entry permission | Conditional | Required if room entry is needed for surprise preparation. |

Rules:

- Do not ask for the guest's budget.
- Do not ask for card information or identity information.
- Accommodation date is not separately required if it can be retrieved from the reservation number.
- If the guest has an accommodation reservation and provides the reservation number, do not create a new reservation.
- If there is no reservation number, ask for reservation information first.
- If the guest needs restaurant setup but has no restaurant reservation, create a restaurant reservation first through the normal restaurant reservation flow and share that reservation number. This only confirms the restaurant reservation, not the special occasion preparation.
- If reservation creation fails or the restaurant mode is manual, create handoff/admin notification with missing fields.
- If the guest refuses to share required fields, create handoff/admin notification with missing fields rather than inventing details.

## Minimum notice periods

| Request type | Minimum notice |
|---|---|
| Birthday | At least 1 day in advance |
| Honeymoon | At least 1 day in advance |
| Anniversary | At least 1 day in advance |
| Marriage proposal | At least 1 day in advance |
| Graduation | At least 1 week in advance |
| Engagement | At least 1 week in advance |
| Wedding | At least 1 week in advance |

Operational rules:

- Same-day requests may only be evaluated subject to availability.
- Special occasion requests can be received during the stay, but representative/admin approval is still required.
- Special occasion services can be offered every day, subject to availability and operational feasibility.
- The system must not say "too late, impossible" unless a policy prohibits the request. It should say that same-day or late requests can only be evaluated by the team.

## Prohibited requests

The following must not be accepted:

- Open flame
- Fireworks
- Torches
- Smoke effects
- Confetti
- Decoration products that may damage room surfaces
- Excessive noise that violates hotel rules
- Music after 22:00
- Preparations that do not match hotel visual standards
- Inappropriate messages, visuals, or concepts

Outside food or beverages:

- The system must not approve outside food or beverages.
- The system must route the matter to reception or a live representative/admin.
- If food safety, allergy, or supplier concerns are present, include them in the admin notification.

Prohibited request response principle:

- Reject the unsafe/prohibited element briefly.
- Offer to forward an alternative safe solution to the team.
- Create admin notification if the request is part of an active special occasion case.

## Human handoff rules

The system must transfer to a live representative/admin in these situations:

- After all required information has been collected and approval is needed.
- Engagement, wedding, graduation, and other special occasion types.
- Corporate celebrations, business dinners, promotion celebrations, and team organizations.
- Child-specific celebrations.
- Group celebrations.
- Questions about pricing, payment, prepayment, deposit, or cancellation policy.
- Any uncertainty.
- Special requests, custom concepts, external suppliers, shopping requests, or guest-provided materials.
- Outside food or beverage requests.
- Room entry permission cases after information is collected.
- Complaints, preparation errors, incomplete preparation, dissatisfaction, or service failure.
- Prohibited or restricted elements.

Handoff behavior:

- If the request can be safely completed by intake first, collect the required fields and then create handoff/admin notification.
- If the request is risky, payment-related, complaint-related, sensitive, or uncertain, create handoff/admin notification immediately with `missing_fields`.
- Every handoff/admin notification must include the complete available context and explicitly list missing fields.
- Once a terminal handoff ticket is created, AI must not keep asking questions or provide parallel advice.

Suggested urgency:

| Situation | Urgency |
|---|---|
| Standard birthday, honeymoon, anniversary intake with advance notice | `medium` |
| Marriage proposal after required fields are collected | `high` |
| Same-day request | `high` |
| Payment/prepayment/deposit/cancellation question | `high` |
| External supplier/custom concept/group/corporate/child-specific event | `high` |
| Complaint, incomplete preparation, dissatisfaction | `high` |
| Privacy/security concern, card/OTP shared, inappropriate content, safety issue | `critical` |

## Admin notification schema

Every admin/representative notification must include these fields.

```json
{
  "notification_type": "special_occasion_request",
  "hotel_id": 21966,
  "conversation_id": "uuid",
  "guest": {
    "full_name": "string | null",
    "phone_number": "string | null (protected admin surface only; never technical logs)",
    "phone_masked": "string | null",
    "phone_hash": "string | null"
  },
  "reservation": {
    "reservation_number": "string | null",
    "reservation_type": "accommodation | restaurant | unknown",
    "restaurant_reservation_number": "string | null",
    "accommodation_reservation_number": "string | null"
  },
  "special_occasion": {
    "type": "birthday | honeymoon | anniversary | marriage_proposal | engagement | graduation | wedding | corporate | business_dinner | promotion | team_organization | child_specific | group | other",
    "date": "YYYY-MM-DD | null",
    "number_of_people": "integer | null",
    "request_details": "string | null",
    "additional_requests": "string | null",
    "allergy_or_food_sensitivity": "string | null",
    "is_surprise": "boolean | null",
    "surprise_for": "string | null",
    "room_entry_required": "boolean | null",
    "room_entry_permission": "granted | denied | not_asked | not_required"
  },
  "workflow": {
    "reason_for_handoff": "string",
    "urgency_level": "medium | high | critical",
    "approval_required": true,
    "pricing_requested": false,
    "payment_topic_detected": false,
    "external_supplier_required": false,
    "prohibited_elements_detected": []
  },
  "missing_fields": [],
  "source": {
    "intent": "special_event_request",
    "state": "NEEDS_VERIFICATION | PENDING_APPROVAL | HANDOFF",
    "risk_flags": ["SPECIAL_EVENT"],
    "transcript_summary": "short safe summary"
  }
}
```

Privacy requirements:

- Admin notification may include operational details needed to fulfill the request.
- Technical logs must not contain raw phone numbers, raw full names, card data, OTP, identity documents, or full message payloads.
- Surprise details must be visible only to the person/team handling the request and must not be disclosed to other guests.

## Customer response templates

Templates must be localized to the guest's language. They must be warm, concise, and clear. They must not contain internal terms such as ticket ID, API, database, risk flag, or backend.

### Intake start - supported type

EN:

> Of course, we would be happy to help with this. Special occasion requests are evaluated based on availability and team approval.  
> Could you please share your reservation number, occasion date, number of people, request details, whether it is a surprise, and any allergy or food sensitivity?

TR:

> Elbette, memnuniyetle yardımcı oluruz. Özel gün talepleri müsaitlik ve ekip onayına göre değerlendirilir.  
> Rezervasyon numaranızı, özel gün tarihini, kişi sayısını, talep detaylarını, sürpriz olup olmadığını ve varsa alerji/gıda hassasiyetini paylaşır mısınız?

### No ready-made package

EN:

> We do not have ready-made packages. Requests are evaluated based on content and availability. I can forward your details to our team for review.

TR:

> Hazır paketlerimiz bulunmuyor. Talepler içerik ve müsaitliğe göre değerlendirilir. Detaylarınızı ekibimize iletebilirim.

### Price/payment question

EN:

> Pricing and payment details are provided only by our live representative after reviewing the request. Please share the occasion details, and I will forward them to our team.

TR:

> Fiyat ve ödeme detayları, talep incelendikten sonra yalnızca canlı temsilcimiz tarafından paylaşılır. Özel gün detaylarını iletirseniz ekibimize aktaracağım.

### Direct human handoff type

EN:

> Thank you for sharing this. This type of organization is reviewed directly by our team. I will forward your request to our live representative for evaluation.

TR:

> Paylaştığınız için teşekkür ederim. Bu tür organizasyonlar doğrudan ekibimiz tarafından değerlendirilir. Talebinizi canlı temsilcimize iletiyorum.

### Same-day request

EN:

> Same-day requests can only be evaluated depending on availability. I will forward the details to our team for review.

TR:

> Aynı gün talepler yalnızca müsaitliğe göre değerlendirilebilir. Detayları ekibimize iletiyorum.

### Prohibited element

EN:

> We are unable to support this element due to hotel safety and operation rules. I would be happy to forward an alternative request to our team.

TR:

> Otel güvenliği ve operasyon kuralları nedeniyle bu unsuru destekleyemiyoruz. Alternatif bir talebi ekibimize iletmekten memnuniyet duyarım.

### Room entry permission

EN:

> If room entry is needed for the preparation, your permission is required. May I note that you allow our team to enter the room for this preparation?

TR:

> Hazırlık için odaya giriş gerekirse izniniz gerekir. Ekibimizin bu hazırlık için odaya girmesine izin verdiğinizi not edebilir miyim?

### Handoff after information collection

EN:

> Thank you. I am forwarding your request to our team for approval. A live representative will review it and assist you as soon as possible.

TR:

> Teşekkür ederim. Talebinizi onay için ekibimize iletiyorum. Canlı temsilcimiz değerlendirme sonrası size yardımcı olacak.

## Approval/rejection messages

Approval message requirements:

- Sent only after live representative/admin approval.
- Must be short, warm, and clear.
- Must summarize the approved request.
- Must explicitly state that it was approved by a live representative/admin.
- Must not include hidden surprise details if the recipient is not the requester.

Approval template:

EN:

> Good news, your special occasion request has been approved by our team.  
> Summary: {occasion_type}, {occasion_date}, {number_of_people} person(s), {short_request_summary}. We look forward to making your occasion special.

TR:

> Güzel haber, özel gün talebiniz ekibimiz tarafından onaylandı.  
> Özet: {occasion_type}, {occasion_date}, {number_of_people} kişi, {short_request_summary}. Bu özel anınızı güzelleştirmekten memnuniyet duyarız.

Rejection message requirements:

- Sent only after representative/admin decision or when a prohibited element must be declined.
- Must preserve this meaning: "We are unable to fulfill this request under the current conditions. However, we would be happy to assist you with an alternative solution."

Rejection template:

EN:

> We are unable to fulfill this request under the current conditions. However, we would be happy to assist you with an alternative solution.

TR:

> Mevcut koşullarda bu talebi yerine getiremiyoruz. Ancak alternatif bir çözüm konusunda memnuniyetle yardımcı oluruz.

## Complaint and dissatisfaction flow

Trigger examples:

- The preparation was not completed.
- The preparation was incomplete.
- The guest is dissatisfied.
- The wrong decoration, cake, name, note, date, or setup was used.
- Surprise information was disclosed to the wrong person.

Automated behavior:

1. Send one short apology message.
2. Immediately create handoff/admin notification.
3. Include reservation number, occasion type, date, complaint summary, guest impact, and urgency.
4. Set urgency to `high`; use `critical` if privacy, safety, harassment, or payment data is involved.
5. Do not argue, blame suppliers, expose internal details, or promise compensation.

Complaint template:

EN:

> We are sorry for this situation. I am immediately forwarding the matter to our team; our live representative will assist you.

TR:

> Bu durum için üzgünüz. Konuyu hemen ekibimize iletiyorum; canlı temsilcimiz size yardımcı olacak.

## Privacy and data security rules

- Surprise information must be shared only with the person who created the request and the authorized hotel team.
- Surprise details must not be shared with other guests.
- Personal messages, photos, gift information, and concept notes must be used only for the request process.
- Personal request materials must be stored only until the process is completed, then deleted or anonymized according to the retention policy.
- Identity information, card details, CVV, OTP, bank password, or sensitive personal data must not be requested.
- If a guest shares card/OTP data, the system must warn the guest not to share it and immediately hand off to the relevant team.
- Phone and name must be masked or hashed in logs.
- Admin notification may include operationally necessary personal details only in protected admin surfaces.
- For child-specific requests, minimize child data. Do not ask for sensitive child information. Use age only if operationally required for cake, setup, seating, or safety.

## Backend decision tree / business logic

Text decision tree:

```text
Incoming message
  -> Detect intent
     -> If not special_event_request: continue normal pipeline
     -> If special_event_request:
        -> Run security/payment/prohibited-content scan
           -> If card/OTP/identity data: warn guest + immediate handoff/admin notification
           -> If complaint/dissatisfaction: apology + immediate handoff/admin notification
           -> If prohibited request: decline prohibited element + notify/handoff if active request
        -> Classify occasion type
           -> If supported type: birthday/honeymoon/anniversary/marriage_proposal
              -> Collect required fields
              -> If missing fields: ask one compact intake question
              -> If room entry needed and permission missing: ask permission
              -> When sufficient info collected: create approval/admin notification
              -> State: PENDING_APPROVAL or HANDOFF depending on implementation
              -> Do not finalize
           -> If handoff-required type: engagement/graduation/wedding/corporate/business/child/group/other
              -> Collect available context if safe and not already terminal
              -> Create handoff/admin notification with missing_fields
              -> State: HANDOFF
              -> Do not price, confirm, or guarantee
        -> If price/payment/prepayment/deposit/cancellation asked at any point:
           -> Do not answer with pricing/payment terms
           -> Create handoff/admin notification
        -> If admin approval event arrives:
           -> If approved: send approved-by-human confirmation
           -> If rejected: send polite rejection/alternative message
```

State rules:

| State | Meaning | Allowed automated action |
|---|---|---|
| `INTENT_DETECTED` | Special occasion intent detected. | Classify type and detect risk. |
| `NEEDS_VERIFICATION` | Required fields missing. | Ask one compact intake question. |
| `READY_FOR_TOOL` | Reservation creation may be needed. | Create restaurant reservation only if needed and supported by normal restaurant flow. |
| `PENDING_APPROVAL` | Required intake complete and human approval requested. | Wait for admin event; no final approval. |
| `HANDOFF` | Live representative/admin must handle. | Send one handoff message; AI stops parallel handling. |
| `CLOSED` | Case resolved or declined. | No further automated special occasion action unless guest starts new request. |

Risk flags:

- Always add `SPECIAL_EVENT` for special occasion requests.
- Add `GROUP_BOOKING` for group celebrations or large party context.
- Add `ALLERGY_ALERT` when allergy, food sensitivity, vegan, gluten-free, lactose, nut, egg, or similar food concern appears.
- Add `PAYMENT_CONFUSION` when price, payment, deposit, prepayment, refund, cancellation charge, or payment method is discussed.
- Add `PHYSICAL_OPERATION_REQUEST` when the guest asks the system to prepare, send, buy, place, decorate, enter room, or arrange materials.
- Add `UNRESOLVED_CASE` when the system lacks reliable policy, tool, or operational capacity.
- Add higher security/privacy flags when sensitive data or safety issues appear.

## Pseudocode or implementable backend rule set

```python
SUPPORTED_TYPES = {
    "birthday",
    "honeymoon",
    "anniversary",
    "marriage_proposal",
}

DIRECT_HANDOFF_TYPES = {
    "engagement",
    "graduation",
    "wedding",
    "corporate_celebration",
    "business_dinner",
    "promotion_celebration",
    "team_organization",
    "children_birthday",
    "child_specific_celebration",
    "group_celebration",
    "other",
}

REQUIRED_FIELDS = {
    "full_name",
    "phone_number",
    "reservation_number",
    "reservation_type",
    "special_occasion_type",
    "special_occasion_date",
    "number_of_people",
    "request_details",
    "additional_requests",
    "is_surprise",
    "allergy_or_food_sensitivity",
}

PROHIBITED_ELEMENTS = {
    "open_flame",
    "fireworks",
    "torches",
    "smoke_effects",
    "confetti",
    "surface_damaging_decoration",
    "excessive_noise",
    "music_after_22_00",
    "inappropriate_content",
    "visual_standards_mismatch",
}


async def handle_special_occasion(context, user_message):
    entities = extract_special_occasion_entities(user_message, context)
    risk_flags = {"SPECIAL_EVENT"}

    if contains_card_or_otp(user_message):
        await warn_payment_data_not_allowed(context)
        return await create_special_occasion_handoff(
            context=context,
            entities=entities,
            risk_flags=risk_flags | {"PAYMENT_CONFUSION"},
            reason="Sensitive payment data shared",
            urgency="critical",
            missing_fields=missing_required_fields(entities),
        )

    if is_complaint_or_dissatisfaction(user_message):
        await send_complaint_apology(context)
        return await create_special_occasion_handoff(
            context=context,
            entities=entities,
            risk_flags=risk_flags,
            reason="Special occasion complaint or dissatisfaction",
            urgency="high",
            missing_fields=missing_required_fields(entities),
        )

    prohibited = detect_prohibited_elements(user_message)
    if prohibited:
        entities["prohibited_elements_detected"] = prohibited
        await send_prohibited_element_message(context)
        # Continue only for safe alternatives; otherwise handoff.
        return await create_special_occasion_handoff(
            context=context,
            entities=entities,
            risk_flags=risk_flags,
            reason="Prohibited or restricted preparation element requested",
            urgency="high",
            missing_fields=missing_required_fields(entities),
        )

    if asks_pricing_or_payment_policy(user_message):
        return await create_special_occasion_handoff(
            context=context,
            entities=entities,
            risk_flags=risk_flags | {"PAYMENT_CONFUSION"},
            reason="Pricing/payment/cancellation information requested",
            urgency="high",
            missing_fields=missing_required_fields(entities),
        )

    occasion_type = normalize_occasion_type(entities.get("special_occasion_type"))
    entities["special_occasion_type"] = occasion_type

    if occasion_type in DIRECT_HANDOFF_TYPES:
        # Do not price, confirm, or guarantee. Admin sees missing fields.
        return await create_special_occasion_handoff(
            context=context,
            entities=entities,
            risk_flags=risk_flags | maybe_group_flag(entities),
            reason="Occasion type requires live representative handling",
            urgency=urgency_for_direct_handoff(entities),
            missing_fields=missing_required_fields(entities),
        )

    missing = missing_required_fields(entities)
    if missing:
        return ask_compact_intake_question(missing, entities)

    if room_entry_needed(entities) and not has_room_entry_permission(entities):
        return ask_room_entry_permission()

    if restaurant_setup_needed(entities) and not has_restaurant_reservation(entities):
        reservation_result = await create_restaurant_reservation_if_allowed(entities)
        if reservation_result.failed:
            return await create_special_occasion_handoff(
                context=context,
                entities=entities,
                risk_flags=risk_flags,
                reason="Restaurant reservation required before special occasion setup",
                urgency="high",
                missing_fields=missing_required_fields(entities),
            )
        entities["restaurant_reservation_number"] = reservation_result.reservation_number

    return await create_special_occasion_approval_notification(
        context=context,
        entities=entities,
        risk_flags=risk_flags | maybe_allergy_flag(entities),
        reason="Special occasion request requires representative/admin approval",
        urgency=urgency_for_supported_type(entities),
    )
```

Approval event handling:

```python
async def handle_special_occasion_admin_event(context, event):
    if event.type != "special_occasion.approval_updated":
        return None

    if event.approved is True:
        return send_guest_message(
            template="special_occasion_approved",
            variables={
                "occasion_type": event.occasion_type,
                "occasion_date": event.occasion_date,
                "number_of_people": event.number_of_people,
                "short_request_summary": event.short_request_summary,
                "approved_by_role": event.approved_by_role,
            },
        )

    return send_guest_message(
        template="special_occasion_rejected",
        variables={
            "alternative_hint": event.alternative_hint,
        },
    )
```

Implementation notes:

- Prefer a dedicated `special_occasion_requests` record when implementing the domain model.
- Until a dedicated tool exists, use `handoff.create_ticket` and `notify.send` with the admin notification schema above.
- Use deterministic dedupe keys, for example: `SPECIAL_EVENT|special_event_request|{reservation_number_or_phone_hash}`.
- Update an existing open request rather than creating duplicate tickets for the same occasion and reservation.
- Store guest phone as hash/masked value in logs; raw phone may appear only in protected admin surfaces if operationally required.
- Customer-facing messages must stay under WhatsApp limits and use one message per turn.

## Edge-case scenarios

| Scenario | Expected behavior |
|---|---|
| Guest asks: "Can you guarantee a birthday setup?" | Do not guarantee. Explain approval/availability requirement and collect required fields. |
| Guest asks only for price of cake. | Do not provide price. Collect occasion details and hand off to representative/admin. |
| Guest asks for fireworks. | Decline prohibited element, offer alternative, notify/handoff if active request. |
| Guest wants same-day proposal dinner. | Collect available details if safe, urgency `high`, handoff/admin notification. |
| Guest wants surprise room decoration but is not the reservation holder. | Do not approve room entry. Handoff for identity/permission handling. |
| Guest gives accommodation reservation number and wants restaurant table decoration. | Do not create new accommodation reservation. If no restaurant reservation exists, create restaurant reservation first if supported, then route occasion approval. |
| Guest has no reservation. | Ask for reservation information or create restaurant reservation first when applicable; no special occasion approval without reservation reference. |
| Guest requests child birthday. | Direct human handoff; minimize child data. |
| Guest shares allergy after cake request. | Add `ALLERGY_ALERT`, include allergy in admin notification, do not recommend menu/cake content unless sourced. |
| Guest sends card number for deposit. | Warn not to share card/OTP data, immediate handoff/admin notification, mask logs. |
| Guest asks to bring outside cake. | Do not approve; route to reception/live representative. |
| Guest requests custom theme with inappropriate message. | Reject inappropriate content and route safe alternatives. |
| Guest complains the preparation was incomplete. | Apologize once, high urgency handoff/admin notification. |
| Admin rejects request. | Send polite rejection/alternative message only after admin event. |
| Admin approves request. | Send short confirmation summarizing request and stating live representative/admin approval. |

## Test scenarios

Use behavior-based tests; do not assert exact free-form wording except for critical safety meanings.

| ID | Input | Expected internal result | Expected guest behavior |
|---|---|---|---|
| SO-001 | "It is my wife's birthday tomorrow. Can you decorate the room?" | `intent=special_event_request`, `risk_flags=["SPECIAL_EVENT"]`, missing fields listed. | Ask compact intake question; no approval/guarantee. |
| SO-002 | Birthday request with all required fields. | Admin notification created, `approval_required=true`, state `PENDING_APPROVAL` or `HANDOFF` depending on implementation. | "Forwarding to team for approval" message. |
| SO-003 | "How much is a birthday cake?" | `PAYMENT_CONFUSION` or pricing trigger; handoff notification with missing fields. | No price; live representative will review. |
| SO-004 | Honeymoon request with reservation number and date. | Missing people/request/allergy/surprise fields detected. | Ask missing fields only. |
| SO-005 | Anniversary restaurant table request, no restaurant reservation. | Restaurant reservation flow triggered if allowed; occasion request remains approval-bound. | Share restaurant reservation number only after restaurant reservation is created; do not approve occasion. |
| SO-006 | Marriage proposal with all fields. | High urgency admin notification/handoff. | Forward to live representative; no finalization. |
| SO-007 | Engagement request. | Direct handoff-required type, ticket/notification created. | No price/confirmation; live representative evaluation. |
| SO-008 | Wedding request 3 days in advance. | Direct handoff, missing/notice risk included. | "Team will evaluate"; no guarantee. |
| SO-009 | Same-day birthday setup. | High urgency, same-day availability note. | "Can only be evaluated subject to availability"; handoff/approval. |
| SO-010 | Request includes fireworks/open flame. | Prohibited element detected. | Decline prohibited element and offer safe alternative. |
| SO-011 | Request includes music after 22:00. | Prohibited/restricted element detected. | Decline restricted element; route alternative if needed. |
| SO-012 | Guest asks to bring own cake/wine. | Outside food/beverage route. | No approval; route to reception/live representative. |
| SO-013 | Guest requests room entry for surprise. | Room entry permission required. | Ask permission if not terminal handoff; otherwise include missing permission in admin notification. |
| SO-014 | Guest refuses to provide reservation number. | Missing required reservation reference; handoff if unresolved. | Ask reservation info once or forward with missing fields. |
| SO-015 | Guest shares card number. | Security/payment data trigger; immediate handoff. | Warn not to share card/OTP; live team handoff. |
| SO-016 | Guest complains setup was not done. | Complaint flow, urgency high, admin notification. | Short apology and immediate live representative routing. |
| SO-017 | Admin approval event. | Approved message generated from event payload. | Short confirmation with request summary and human approval statement. |
| SO-018 | Admin rejection event. | Rejection message generated from event payload. | Polite alternative-oriented rejection. |
| SO-019 | Duplicate messages for same reservation/occasion. | Same dedupe key; update existing ticket/request. | No duplicate handoff spam. |
| SO-020 | Long custom concept request. | Custom/external supplier flag; handoff. | No feasibility promise; representative review. |

Acceptance criteria:

- No automated path finalizes a special occasion request.
- No automated path shares prices or payment terms.
- Admin notification always includes available required fields and `missing_fields`.
- Prohibited elements are never accepted.
- Surprise/privacy rules are enforced.
- Complaint flow always creates immediate human handoff/admin visibility.
- Approval/rejection guest messages are sent only from admin/representative decision events.
