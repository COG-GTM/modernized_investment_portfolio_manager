CREATE TABLE "history" (
	"portfolio_id" varchar(8) NOT NULL,
	"date" varchar(8) NOT NULL,
	"time" varchar(6) NOT NULL,
	"seq_no" varchar(4) NOT NULL,
	"record_type" varchar(2),
	"action_code" varchar(1),
	"before_image" text,
	"after_image" text,
	"reason_code" varchar(4),
	"process_date" timestamp,
	"process_user" varchar(8),
	CONSTRAINT "history_portfolio_id_date_time_seq_no_pk" PRIMARY KEY("portfolio_id","date","time","seq_no"),
	CONSTRAINT "ck_history_record_type" CHECK ("history"."record_type" IN ('PT', 'PS', 'TR')),
	CONSTRAINT "ck_history_action_code" CHECK ("history"."action_code" IN ('A', 'C', 'D'))
);
--> statement-breakpoint
CREATE TABLE "portfolios" (
	"port_id" varchar(8) NOT NULL,
	"account_no" varchar(10) NOT NULL,
	"client_name" varchar(30),
	"client_type" varchar(1),
	"create_date" date,
	"last_maint" date,
	"status" varchar(1),
	"total_value" numeric(15, 2),
	"cash_balance" numeric(15, 2),
	"last_user" varchar(8),
	"last_trans" varchar(8),
	CONSTRAINT "portfolios_port_id_account_no_pk" PRIMARY KEY("port_id","account_no"),
	CONSTRAINT "uq_portfolio_port_id" UNIQUE("port_id"),
	CONSTRAINT "ck_portfolio_client_type" CHECK ("portfolios"."client_type" IN ('I', 'C', 'T')),
	CONSTRAINT "ck_portfolio_status" CHECK ("portfolios"."status" IN ('A', 'C', 'S'))
);
--> statement-breakpoint
CREATE TABLE "positions" (
	"portfolio_id" varchar(8) NOT NULL,
	"date" date NOT NULL,
	"investment_id" varchar(10) NOT NULL,
	"quantity" numeric(15, 4),
	"cost_basis" numeric(15, 2),
	"market_value" numeric(15, 2),
	"currency" varchar(3),
	"status" varchar(1),
	"last_maint_date" timestamp,
	"last_maint_user" varchar(8),
	CONSTRAINT "positions_portfolio_id_date_investment_id_pk" PRIMARY KEY("portfolio_id","date","investment_id"),
	CONSTRAINT "ck_position_status" CHECK ("positions"."status" IN ('A', 'C', 'P'))
);
--> statement-breakpoint
CREATE TABLE "transactions" (
	"date" date NOT NULL,
	"time" time NOT NULL,
	"portfolio_id" varchar(8) NOT NULL,
	"sequence_no" varchar(6) NOT NULL,
	"investment_id" varchar(10),
	"type" varchar(2),
	"quantity" numeric(15, 4),
	"price" numeric(15, 4),
	"amount" numeric(15, 2),
	"currency" varchar(3),
	"status" varchar(1),
	"process_date" timestamp,
	"process_user" varchar(8),
	CONSTRAINT "transactions_date_time_portfolio_id_sequence_no_pk" PRIMARY KEY("date","time","portfolio_id","sequence_no"),
	CONSTRAINT "ck_transaction_type" CHECK ("transactions"."type" IN ('BU', 'SL', 'TR', 'FE')),
	CONSTRAINT "ck_transaction_status" CHECK ("transactions"."status" IN ('P', 'D', 'F', 'R'))
);
--> statement-breakpoint
ALTER TABLE "history" ADD CONSTRAINT "fk_history_portfolio" FOREIGN KEY ("portfolio_id") REFERENCES "public"."portfolios"("port_id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "positions" ADD CONSTRAINT "fk_position_portfolio" FOREIGN KEY ("portfolio_id") REFERENCES "public"."portfolios"("port_id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "fk_transaction_portfolio" FOREIGN KEY ("portfolio_id") REFERENCES "public"."portfolios"("port_id") ON DELETE no action ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "idx_history_portfolio_id" ON "history" USING btree ("portfolio_id");--> statement-breakpoint
CREATE INDEX "idx_history_date" ON "history" USING btree ("date");--> statement-breakpoint
CREATE INDEX "idx_history_record_type" ON "history" USING btree ("record_type");--> statement-breakpoint
CREATE INDEX "idx_history_action_code" ON "history" USING btree ("action_code");--> statement-breakpoint
CREATE INDEX "idx_portfolio_status" ON "portfolios" USING btree ("status");--> statement-breakpoint
CREATE INDEX "idx_portfolio_client_type" ON "portfolios" USING btree ("client_type");--> statement-breakpoint
CREATE INDEX "idx_position_portfolio_id" ON "positions" USING btree ("portfolio_id");--> statement-breakpoint
CREATE INDEX "idx_position_date" ON "positions" USING btree ("date");--> statement-breakpoint
CREATE INDEX "idx_position_investment_id" ON "positions" USING btree ("investment_id");--> statement-breakpoint
CREATE INDEX "idx_position_status" ON "positions" USING btree ("status");--> statement-breakpoint
CREATE INDEX "idx_transaction_portfolio_id" ON "transactions" USING btree ("portfolio_id");--> statement-breakpoint
CREATE INDEX "idx_transaction_date" ON "transactions" USING btree ("date");--> statement-breakpoint
CREATE INDEX "idx_transaction_investment_id" ON "transactions" USING btree ("investment_id");--> statement-breakpoint
CREATE INDEX "idx_transaction_type" ON "transactions" USING btree ("type");--> statement-breakpoint
CREATE INDEX "idx_transaction_status" ON "transactions" USING btree ("status");