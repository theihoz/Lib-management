// Typed wrappers over generated paths. Re-run `npm run gen:api` after contract changes.
import type { FetchOptions } from "openapi-fetch";
import type { ApiClient } from "./client";
import type { paths } from "./schema";

export function createServices(client: ApiClient) {
  return {
    catalog: {
      get_copies_lookup: (options: FetchOptions<paths["/api/v1/copies/lookup"]["get"]>) =>
        client.GET("/api/v1/copies/lookup", options),
      patch_copies_id: (options: FetchOptions<paths["/api/v1/copies/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/copies/{id}", options),
      get_locations: (options: FetchOptions<paths["/api/v1/locations"]["get"]>) =>
        client.GET("/api/v1/locations", options),
      post_locations: (options: FetchOptions<paths["/api/v1/locations"]["post"]>) =>
        client.POST("/api/v1/locations", options),
      get_book_editions: (options: FetchOptions<paths["/api/v1/book-editions"]["get"]>) =>
        client.GET("/api/v1/book-editions", options),
      post_book_editions: (options: FetchOptions<paths["/api/v1/book-editions"]["post"]>) =>
        client.POST("/api/v1/book-editions", options),
      get_book_editions_id: (options: FetchOptions<paths["/api/v1/book-editions/{id}"]["get"]>) =>
        client.GET("/api/v1/book-editions/{id}", options),
      patch_book_editions_id: (
        options: FetchOptions<paths["/api/v1/book-editions/{id}"]["patch"]>,
      ) => client.PATCH("/api/v1/book-editions/{id}", options),
      get_authors: (options: FetchOptions<paths["/api/v1/authors"]["get"]>) =>
        client.GET("/api/v1/authors", options),
      post_authors: (options: FetchOptions<paths["/api/v1/authors"]["post"]>) =>
        client.POST("/api/v1/authors", options),
      get_authors_id: (options: FetchOptions<paths["/api/v1/authors/{id}"]["get"]>) =>
        client.GET("/api/v1/authors/{id}", options),
      patch_authors_id: (options: FetchOptions<paths["/api/v1/authors/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/authors/{id}", options),
      get_publishers: (options: FetchOptions<paths["/api/v1/publishers"]["get"]>) =>
        client.GET("/api/v1/publishers", options),
      post_publishers: (options: FetchOptions<paths["/api/v1/publishers"]["post"]>) =>
        client.POST("/api/v1/publishers", options),
      get_publishers_id: (options: FetchOptions<paths["/api/v1/publishers/{id}"]["get"]>) =>
        client.GET("/api/v1/publishers/{id}", options),
      patch_publishers_id: (options: FetchOptions<paths["/api/v1/publishers/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/publishers/{id}", options),
      get_categories: (options: FetchOptions<paths["/api/v1/categories"]["get"]>) =>
        client.GET("/api/v1/categories", options),
      post_categories: (options: FetchOptions<paths["/api/v1/categories"]["post"]>) =>
        client.POST("/api/v1/categories", options),
      get_categories_id: (options: FetchOptions<paths["/api/v1/categories/{id}"]["get"]>) =>
        client.GET("/api/v1/categories/{id}", options),
      patch_categories_id: (options: FetchOptions<paths["/api/v1/categories/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/categories/{id}", options),
      post_book_editions_id_copies: (
        options: FetchOptions<paths["/api/v1/book-editions/{id}/copies"]["post"]>,
      ) => client.POST("/api/v1/book-editions/{id}/copies", options),
      get_book_editions_id_copies: (
        options: FetchOptions<paths["/api/v1/book-editions/{id}/copies"]["get"]>,
      ) => client.GET("/api/v1/book-editions/{id}/copies", options),
      post_media_upload_intents: (
        options: FetchOptions<paths["/api/v1/media-upload-intents"]["post"]>,
      ) => client.POST("/api/v1/media-upload-intents", options),
      post_media_assets_id_finalization: (
        options: FetchOptions<paths["/api/v1/media-assets/{id}/finalization"]["post"]>,
      ) => client.POST("/api/v1/media-assets/{id}/finalization", options),
    },
    readers: {
      get_readers_lookup: (options: FetchOptions<paths["/api/v1/readers/lookup"]["get"]>) =>
        client.GET("/api/v1/readers/lookup", options),
      get_readers: (options: FetchOptions<paths["/api/v1/readers"]["get"]>) =>
        client.GET("/api/v1/readers", options),
      post_readers: (options: FetchOptions<paths["/api/v1/readers"]["post"]>) =>
        client.POST("/api/v1/readers", options),
      get_readers_id: (options: FetchOptions<paths["/api/v1/readers/{id}"]["get"]>) =>
        client.GET("/api/v1/readers/{id}", options),
      patch_readers_id: (options: FetchOptions<paths["/api/v1/readers/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/readers/{id}", options),
      post_readers_id_cards: (options: FetchOptions<paths["/api/v1/readers/{id}/cards"]["post"]>) =>
        client.POST("/api/v1/readers/{id}/cards", options),
      get_readers_id_eligibility: (
        options: FetchOptions<paths["/api/v1/readers/{id}/eligibility"]["get"]>,
      ) => client.GET("/api/v1/readers/{id}/eligibility", options),
      get_readers_id_cards: (options: FetchOptions<paths["/api/v1/readers/{id}/cards"]["get"]>) =>
        client.GET("/api/v1/readers/{id}/cards", options),
      patch_reader_cards_id: (options: FetchOptions<paths["/api/v1/reader-cards/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/reader-cards/{id}", options),
    },
    circulation: {
      post_loans: (options: FetchOptions<paths["/api/v1/loans"]["post"]>) =>
        client.POST("/api/v1/loans", options),
      get_loans: (options: FetchOptions<paths["/api/v1/loans"]["get"]>) =>
        client.GET("/api/v1/loans", options),
      get_loans_id: (options: FetchOptions<paths["/api/v1/loans/{id}"]["get"]>) =>
        client.GET("/api/v1/loans/{id}", options),
      post_returns: (options: FetchOptions<paths["/api/v1/returns"]["post"]>) =>
        client.POST("/api/v1/returns", options),
      post_loans_id_renewals: (
        options: FetchOptions<paths["/api/v1/loans/{id}/renewals"]["post"]>,
      ) => client.POST("/api/v1/loans/{id}/renewals", options),
      post_reservations: (options: FetchOptions<paths["/api/v1/reservations"]["post"]>) =>
        client.POST("/api/v1/reservations", options),
      get_reservations: (options: FetchOptions<paths["/api/v1/reservations"]["get"]>) =>
        client.GET("/api/v1/reservations", options),
      post_reservations_id_cancellations: (
        options: FetchOptions<paths["/api/v1/reservations/{id}/cancellations"]["post"]>,
      ) => client.POST("/api/v1/reservations/{id}/cancellations", options),
      post_reservations_id_pickups: (
        options: FetchOptions<paths["/api/v1/reservations/{id}/pickups"]["post"]>,
      ) => client.POST("/api/v1/reservations/{id}/pickups", options),
      get_readers_id_history: (
        options: FetchOptions<paths["/api/v1/readers/{id}/history"]["get"]>,
      ) => client.GET("/api/v1/readers/{id}/history", options),
      get_me_loans: (options: FetchOptions<paths["/api/v1/me/loans"]["get"]>) =>
        client.GET("/api/v1/me/loans", options),
      get_me_reservations: (options: FetchOptions<paths["/api/v1/me/reservations"]["get"]>) =>
        client.GET("/api/v1/me/reservations", options),
    },
    finance: {
      get_fine_charges: (options: FetchOptions<paths["/api/v1/fine-charges"]["get"]>) =>
        client.GET("/api/v1/fine-charges", options),
      post_charge_assessments: (
        options: FetchOptions<paths["/api/v1/charge-assessments"]["post"]>,
      ) => client.POST("/api/v1/charge-assessments", options),
      get_charge_assessments: (options: FetchOptions<paths["/api/v1/charge-assessments"]["get"]>) =>
        client.GET("/api/v1/charge-assessments", options),
      post_charge_assessments_id_decisions: (
        options: FetchOptions<paths["/api/v1/charge-assessments/{id}/decisions"]["post"]>,
      ) => client.POST("/api/v1/charge-assessments/{id}/decisions", options),
      post_payments: (options: FetchOptions<paths["/api/v1/payments"]["post"]>) =>
        client.POST("/api/v1/payments", options),
      post_fine_charges_id_waivers: (
        options: FetchOptions<paths["/api/v1/fine-charges/{id}/waivers"]["post"]>,
      ) => client.POST("/api/v1/fine-charges/{id}/waivers", options),
      post_ledger_reversals: (options: FetchOptions<paths["/api/v1/ledger-reversals"]["post"]>) =>
        client.POST("/api/v1/ledger-reversals", options),
      get_me_fine_charges: (options: FetchOptions<paths["/api/v1/me/fine-charges"]["get"]>) =>
        client.GET("/api/v1/me/fine-charges", options),
    },
    reports: {
      get_dashboard: (options: FetchOptions<paths["/api/v1/dashboard"]["get"]>) =>
        client.GET("/api/v1/dashboard", options),
      get_overdue_items: (options: FetchOptions<paths["/api/v1/overdue-items"]["get"]>) =>
        client.GET("/api/v1/overdue-items", options),
      post_report_jobs: (options: FetchOptions<paths["/api/v1/report-jobs"]["post"]>) =>
        client.POST("/api/v1/report-jobs", options),
      post_export_jobs: (options: FetchOptions<paths["/api/v1/export-jobs"]["post"]>) =>
        client.POST("/api/v1/export-jobs", options),
      get_report_jobs_id_result: (
        options: FetchOptions<paths["/api/v1/report-jobs/{id}/result"]["get"]>,
      ) => client.GET("/api/v1/report-jobs/{id}/result", options),
      get_export_jobs_id_content: (
        options: FetchOptions<paths["/api/v1/export-jobs/{id}/content"]["get"]>,
      ) => client.GET("/api/v1/export-jobs/{id}/content", { ...options, parseAs: "blob" }),
      get_jobs_id: (options: FetchOptions<paths["/api/v1/jobs/{id}"]["get"]>) =>
        client.GET("/api/v1/jobs/{id}", options),
      get_report_jobs_id: (options: FetchOptions<paths["/api/v1/report-jobs/{id}"]["get"]>) =>
        client.GET("/api/v1/report-jobs/{id}", options),
      get_export_jobs_id_download: (
        options: FetchOptions<paths["/api/v1/export-jobs/{id}/download"]["get"]>,
      ) => client.GET("/api/v1/export-jobs/{id}/download", options),
      post_policy_versions: (options: FetchOptions<paths["/api/v1/policy-versions"]["post"]>) =>
        client.POST("/api/v1/policy-versions", options),
      get_policy_versions: (options: FetchOptions<paths["/api/v1/policy-versions"]["get"]>) =>
        client.GET("/api/v1/policy-versions", options),
      post_policy_versions_id_approval: (
        options: FetchOptions<paths["/api/v1/policy-versions/{id}/approval"]["post"]>,
      ) => client.POST("/api/v1/policy-versions/{id}/approval", options),
    },
    identity: {
      get_auth_me: (options: FetchOptions<paths["/api/v1/auth/me"]["get"]>) =>
        client.GET("/api/v1/auth/me", options),
      post_accounts_reader_provisioning: (
        options: FetchOptions<paths["/api/v1/accounts/reader-provisioning"]["post"]>,
      ) => client.POST("/api/v1/accounts/reader-provisioning", options),
      get_accounts: (options: FetchOptions<paths["/api/v1/accounts"]["get"]>) =>
        client.GET("/api/v1/accounts", options),
      patch_accounts_id: (options: FetchOptions<paths["/api/v1/accounts/{id}"]["patch"]>) =>
        client.PATCH("/api/v1/accounts/{id}", options),
      put_accounts_id_roles: (options: FetchOptions<paths["/api/v1/accounts/{id}/roles"]["put"]>) =>
        client.PUT("/api/v1/accounts/{id}/roles", options),
      get_roles: (options: FetchOptions<paths["/api/v1/roles"]["get"]>) =>
        client.GET("/api/v1/roles", options),
      post_roles: (options: FetchOptions<paths["/api/v1/roles"]["post"]>) =>
        client.POST("/api/v1/roles", options),
      put_roles_id_permissions: (
        options: FetchOptions<paths["/api/v1/roles/{id}/permissions"]["put"]>,
      ) => client.PUT("/api/v1/roles/{id}/permissions", options),
      get_permissions: (options: FetchOptions<paths["/api/v1/permissions"]["get"]>) =>
        client.GET("/api/v1/permissions", options),
    },
    inventory: {
      post_acquisition_receipts: (
        options: FetchOptions<paths["/api/v1/acquisition-receipts"]["post"]>,
      ) => client.POST("/api/v1/acquisition-receipts", options),
      get_acquisition_receipts: (
        options: FetchOptions<paths["/api/v1/acquisition-receipts"]["get"]>,
      ) => client.GET("/api/v1/acquisition-receipts", options),
      post_acquisition_receipts_id_approval: (
        options: FetchOptions<paths["/api/v1/acquisition-receipts/{id}/approval"]["post"]>,
      ) => client.POST("/api/v1/acquisition-receipts/{id}/approval", options),
      post_acquisition_receipts_id_posting: (
        options: FetchOptions<paths["/api/v1/acquisition-receipts/{id}/posting"]["post"]>,
      ) => client.POST("/api/v1/acquisition-receipts/{id}/posting", options),
      post_copies_id_disposal: (
        options: FetchOptions<paths["/api/v1/copies/{id}/disposal"]["post"]>,
      ) => client.POST("/api/v1/copies/{id}/disposal", options),
    },
    operations: {
      post_backup_jobs: (options: FetchOptions<paths["/api/v1/backup-jobs"]["post"]>) =>
        client.POST("/api/v1/backup-jobs", options),
      get_backup_manifests: (options: FetchOptions<paths["/api/v1/backup-manifests"]["get"]>) =>
        client.GET("/api/v1/backup-manifests", options),
      post_restore_jobs: (options: FetchOptions<paths["/api/v1/restore-jobs"]["post"]>) =>
        client.POST("/api/v1/restore-jobs", options),
      post_restore_jobs_id_approval: (
        options: FetchOptions<paths["/api/v1/restore-jobs/{id}/approval"]["post"]>,
      ) => client.POST("/api/v1/restore-jobs/{id}/approval", options),
      get_jobs_id: (options: FetchOptions<paths["/api/v1/jobs/{id}"]["get"]>) =>
        client.GET("/api/v1/jobs/{id}", options),
      post_jobs_id_replay: (options: FetchOptions<paths["/api/v1/jobs/{id}/replay"]["post"]>) =>
        client.POST("/api/v1/jobs/{id}/replay", options),
    },
    notifications: {
      get_me_notifications: (options: FetchOptions<paths["/api/v1/me/notifications"]["get"]>) =>
        client.GET("/api/v1/me/notifications", options),
      post_me_notifications_id_read: (
        options: FetchOptions<paths["/api/v1/me/notifications/{id}/read"]["post"]>,
      ) => client.POST("/api/v1/me/notifications/{id}/read", options),
      put_me_notification_preferences: (
        options: FetchOptions<paths["/api/v1/me/notification-preferences"]["put"]>,
      ) => client.PUT("/api/v1/me/notification-preferences", options),
    },
    health: {
      health_live: (options: FetchOptions<paths["/health/live"]["get"]>) =>
        client.GET("/health/live", options),
      health_ready: (options: FetchOptions<paths["/health/ready"]["get"]>) =>
        client.GET("/health/ready", options),
    },
  };
}
export type ApiServices = ReturnType<typeof createServices>;
