package com.jakubsuran.aicoachapi.shared.security;

import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.RequestScope;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
@RequestScope
public class HeaderCurrentUserProvider implements CurrentUserProvider {
	private static final String USER_ID_HEADER = "X-User-Id";

	@Override
	public String currentUserId() {
		var attributes = RequestContextHolder.getRequestAttributes();
		if (!(attributes instanceof ServletRequestAttributes servletAttributes)) {
			throw new AuthenticationRequiredException("Authentication is required.");
		}

		var userId = servletAttributes.getRequest().getHeader(USER_ID_HEADER);
		if (userId == null || userId.isBlank()) {
			throw new AuthenticationRequiredException("X-User-Id header is required.");
		}

		return userId.trim();
	}
}
