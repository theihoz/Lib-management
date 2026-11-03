import { Badge, Button, Notice, Panel } from "../ui/components";
import { Icon } from "../ui/Icon";
import type { ViewProps } from "./types";
import { CatalogView, BookView, CategoriesView, UploadView } from "./CatalogViews";
import { ProfileView, PortalView, NotificationsView, PreferencesView, HistoryView } from "./PeopleViews";
import { CheckoutView, ReturnsView, LoanView, HoldView } from "./CirculationViews";
import { FinanceView, PaymentView, AssessmentView } from "./FinanceViews";
import { ReportsView, PolicyView, PermissionsView, AcquisitionView } from "./ManagementViews";
import { JobView, BackupView, RestoreView } from "./OperationsViews";
import { FormView, ListView, PreviewAction, ReceiptView } from "./shared";

const views: Record<string, React.ComponentType<ViewProps>> = {
  catalog: CatalogView, book: BookView, list: ListView, form: FormView, tree: CategoriesView,
  upload: UploadView, profile: ProfileView, ownprofile: ProfileView, checkout: CheckoutView,
  returns: ReturnsView, loan: LoanView, ownloans: LoanView, renew: LoanView, receipt: ReceiptView,
  hold: HoldView, ownholds: HoldView, finance: FinanceView, ownfinance: FinanceView,
  payment: PaymentView, assessment: AssessmentView, portal: PortalView, notifications: NotificationsView,
  preferences: PreferencesView, history: HistoryView, reports: ReportsView, policy: PolicyView,
  permissions: PermissionsView, acquisition: AcquisitionView, job: JobView, backup: BackupView, restore: RestoreView,
};
const authMessages: Record<string, string> = {
  "FE01.01": "Sử dụng tài khoản được nhân viên cấp hoặc liên kết.",
  "FE01.02": "Đang chuyển về trang làm việc của bạn.",
  "FE01.03": "Đăng nhập lại để tiếp tục. Dữ liệu biểu mẫu chưa gửi được giữ lại.",
  "FE01.04": "Tài khoản hiện tại không có quyền thực hiện thao tác này.",
  "FE01.05": "Liên hệ quản trị viên để kiểm tra trạng thái tài khoản.",
  "FE01.06": "Kiểm tra kết nối mạng rồi thử lại. Không cần nhập lại biểu mẫu.",
  "FE01.07": "Bạn sẽ kết thúc phiên làm việc trên trình duyệt này.",
};
function AuthDesignView({ screen, preview, navigate }: ViewProps) {
  return <div className="auth-layout"><div className="auth-editorial"><span className="eyebrow">LIB / MANAGEMENT</span><Icon name="book" size={64} /><h2>Một tài khoản.<br /><em>Cả thư viện.</em></h2><p>Không gian cho những cuốn sách,<br />và những người yêu đọc.</p></div><Panel className="auth-card"><Badge>{screen.id === "FE01.01" ? "TÀI KHOẢN THƯ VIỆN" : "TRẠNG THÁI PHIÊN"}</Badge><h2>{screen.title}</h2><p className="muted">{authMessages[screen.id]}</p><div className="actions"><PreviewAction preview={preview}>{screen.action ?? "Tiếp tục"}</PreviewAction></div><p className="muted">Cần hỗ trợ? Liên hệ nhân viên thư viện.</p>{screen.id !== "FE01.01" && <Button variant="ghost" onClick={() => navigate?.("FE01.01")}>Về trang đăng nhập</Button>}</Panel></div>;
}
export function FeatureView(props: ViewProps) {
  const View = props.screen.kind === "auth" ? AuthDesignView : views[props.screen.kind];
  const safeProps = { ...props, sample: props.preview ? props.sample : undefined };
  return <section className="feature-view stack" role="region" aria-label={props.screen.title}>{!props.preview && !props.screen.implemented && <Notice>Chức năng đang được chuẩn bị. Thông tin và thao tác sẽ khả dụng khi thư viện mở chức năng này.</Notice>}{View ? <View {...safeProps} /> : <Notice tone="warning">Màn hình chưa khả dụng.</Notice>}{props.screen.note && <p className="page-note"><Icon name="alert" size={16} />{props.screen.note}</p>}</section>;
}
