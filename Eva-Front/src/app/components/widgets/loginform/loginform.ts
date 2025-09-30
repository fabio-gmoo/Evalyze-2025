import { Component, inject, signal, computed, EventEmitter, Output } from '@angular/core';
import {
  ReactiveFormsModule,
  FormBuilder,
  Validators,
  NonNullableFormBuilder,
} from '@angular/forms';
import { Auth } from '@services/auth';
import { Router, RouterLink } from '@angular/router';

type Role = 'company' | 'candidate';

@Component({
  selector: 'app-loginform',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './loginform.html',
  styleUrl: './loginform.scss',
})
export class Loginform {
  @Output() loginSuccess = new EventEmitter<void>();

  show = signal(false);
  loading = signal(false);
  errorMsg = signal<string | null>(null);

  private fb: NonNullableFormBuilder = inject(FormBuilder).nonNullable;
  private auth = inject(Auth);
  private router = inject(Router);

  form = this.fb.group({
    email: this.fb.control('', { validators: [Validators.required, Validators.email] }),
    password: this.fb.control('', { validators: [Validators.required, Validators.minLength(6)] }),
    remember: this.fb.control(false),
    role: this.fb.control<Role>('company'),
  });

  disabled = computed(() => this.loading() || this.form.invalid);

  toggleShow() {
    this.show.set(!this.show());
  }

  setRole(r: Role) {
    this.form.controls.role.setValue(r);
  }

  submit() {
    if (this.loading() || this.form.invalid) return;

    this.loading.set(true);
    this.errorMsg.set(null);

    const { email, password, role } = this.form.getRawValue(); // ← Incluir role

    this.auth.login({ email, password, role }).subscribe({
      next: (user) => {
        console.log('Login exitoso, usuario:', user);
        this.loginSuccess.emit();
        this.router.navigate(['/vacantes']);
      },
      error: (err) => {
        console.error('Error en login:', err);
        this.errorMsg.set(err?.error?.detail ?? 'No se pudo iniciar sesión');
        this.loading.set(false);
      },
      complete: () => {
        this.loading.set(false);
      },
    });
  }
}
