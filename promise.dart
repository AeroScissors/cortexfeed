// File: lib/core/models/promise.dart
enum PromiseStatus { active, completed, }

class Promise {
  final String id;
  final String statement;
  final DateTime statedAt;

  // ownership
  final String createdByUserId;

  // operational state
  final PromiseStatus status;
  final DateTime? intendedDate;
  final DateTime? completedAt;

  // resolution details
  final String? resolutionType; // 'kept_full' | 'kept_partial' | 'not_kept'
  final String? resolvedByUserId; // userId
  final String? resolutionNote; // optional private note

  // acknowledgment details
  final DateTime? acknowledgedAt;
  final String? acknowledgedByUserId;

  // Passive presence metadata
  final DateTime? lastViewedAt;
  final int passiveViewCount;
  final DateTime? lastInteractionAt;

  const Promise({
    required this.id,
    required this.statement,
    required this.statedAt,
    required this.createdByUserId,
    this.status = PromiseStatus.active,
    this.intendedDate,
    this.completedAt,
    this.resolutionType,
    this.resolvedByUserId,
    this.resolutionNote,
    this.acknowledgedAt,
    this.acknowledgedByUserId,
    this.lastViewedAt,
    this.passiveViewCount = 0,
    this.lastInteractionAt,
  });

  // Derived helpers
  bool get isActive => status == PromiseStatus.active;
  bool get isCompleted => status == PromiseStatus.completed;

  // Compatibility helpers for UI code from previous steps
  DateTime? get resolvedAt => completedAt;
  String? get resolutionLabel => resolutionType;

  Promise registerPassiveView(DateTime now) {
    return copyWith(
      lastViewedAt: now,
      passiveViewCount: passiveViewCount + 1,
    );
  }

  Promise registerInteraction(DateTime now) {
    return copyWith(
      lastInteractionAt: now,
    );
  }

  Promise copyWith({
    String? id,
    String? statement,
    DateTime? statedAt,
    String? createdByUserId,
    PromiseStatus? status,
    DateTime? intendedDate,
    DateTime? completedAt,
    String? resolutionType,
    String? resolvedByUserId,
    String? resolutionNote,
    DateTime? acknowledgedAt,
    String? acknowledgedByUserId,
    DateTime? lastViewedAt,
    int? passiveViewCount,
    DateTime? lastInteractionAt,
  }) {
    return Promise(
      id: id ?? this.id,
      statement: statement ?? this.statement,
      statedAt: statedAt ?? this.statedAt,
      createdByUserId: createdByUserId ?? this.createdByUserId,
      status: status ?? this.status,
      intendedDate: intendedDate ?? this.intendedDate,
      completedAt: completedAt ?? this.completedAt,
      resolutionType: resolutionType ?? this.resolutionType,
      resolvedByUserId: resolvedByUserId ?? this.resolvedByUserId,
      resolutionNote: resolutionNote ?? this.resolutionNote,
      acknowledgedAt: acknowledgedAt ?? this.acknowledgedAt,
      acknowledgedByUserId: acknowledgedByUserId ?? this.acknowledgedByUserId,
      lastViewedAt: lastViewedAt ?? this.lastViewedAt,
      passiveViewCount: passiveViewCount ?? this.passiveViewCount,
      lastInteractionAt: lastInteractionAt ?? this.lastInteractionAt,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'statement': statement,
      'stated_at': statedAt.toIso8601String(),
      'created_by_user_id': createdByUserId,
      'status': status.name,
      'intended_date': intendedDate?.toIso8601String(),
      'completed_at': completedAt?.toIso8601String(),
      'resolution_type': resolutionType,
      'resolved_by_user_id': resolvedByUserId,
      'resolution_note': resolutionNote,
      'acknowledged_at': acknowledgedAt?.toIso8601String(),
      'acknowledged_by_user_id': acknowledgedByUserId,
      'last_viewed_at': lastViewedAt?.toIso8601String(),
      'passive_view_count': passiveViewCount,
      'last_interaction_at': lastInteractionAt?.toIso8601String(),
    };
  }

  static Promise fromMap(Map<String, dynamic> map) {
    return Promise(
      id: (map['id'] ?? map['promise_id'] ?? '') as String,

      statement: (map['statement'] ?? map['title'] ?? '') as String,

      statedAt: DateTime.parse(
        (map['stated_at'] ?? map['created_at'] ?? DateTime.now().toIso8601String()) as String,
      ),

      createdByUserId: (
        map['created_by_user_id'] ??
        map['created_by'] ??
        map['fromUserId'] ??
        ''
      ) as String,

      // FIX 1: server sends 'resolved', not 'completed'
      status: (
              map['status'] == 'completed' ||
              map['status'] == 'resolved' ||
              map['is_completed'] == true ||
              map['resolutionType'] != null ||
              map['resolution_type'] != null
            )
          ? PromiseStatus.completed
          : PromiseStatus.active,

      // FIX 2: server uses 'due_at', not 'intended_date'
      intendedDate: (map['intended_date'] ?? map['due_at']) != null
          ? DateTime.parse((map['intended_date'] ?? map['due_at']) as String)
          : null,

      // FIX 3: server uses 'resolved_at', not 'completed_at'
      completedAt: (map['completedAt'] ?? map['completed_at'] ?? map['resolved_at']) != null
          ? DateTime.parse((map['completedAt'] ?? map['completed_at'] ?? map['resolved_at']) as String)
          : null,

      resolutionType: (map['resolutionType'] ?? map['resolution_type']) as String?,

      resolvedByUserId: (map['resolvedByUserId'] ?? map['resolved_by_user_id']) as String?,

      resolutionNote: map['resolution_note'] != null
          ? (map['resolution_note'] as String)
          : null,

      acknowledgedAt: map['acknowledged_at'] != null
          ? DateTime.parse(map['acknowledged_at'])
          : null,

      acknowledgedByUserId: map['acknowledged_by_user_id'] != null
          ? (map['acknowledged_by_user_id'] as String)
          : null,

      lastViewedAt: map['last_viewed_at'] != null
          ? DateTime.parse(map['last_viewed_at'])
          : null,

      passiveViewCount: (map['passive_view_count'] ?? 0) as int,

      lastInteractionAt: map['last_interaction_at'] != null
          ? DateTime.parse(map['last_interaction_at'])
          : null,
    );
  }
}
